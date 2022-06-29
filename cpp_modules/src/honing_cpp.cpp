#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <algorithm>
#include <unordered_map>
#include <vector>

struct Enhancement {
  long rate;
  long max_amount;
  double price;
};

struct State {
  long honing_rate;
  long artisans_points;

  bool operator==(const State &p) const {
    return honing_rate == p.honing_rate && artisans_points == p.artisans_points;
  }

  bool operator!=(const State &p) const {
    return honing_rate != p.honing_rate || artisans_points != p.artisans_points;
  }
};

static const long MAX_ARTISANS_POINTS = 21506;
static const long MYRIA = 10000;
static const long BOOK_RATE = 1000;
static const double MAX_PRICE = -1.0;
static const State GUARANTEED_SUCCESS = {-1, -1};

struct hash_state {
  std::size_t operator()(const State &state) const {
    std::size_t h1 = std::hash<int>()(state.honing_rate);
    std::size_t h2 = std::hash<int>()(state.artisans_points);
    return h1 ^ h2;
  }
};

using Combination = std::vector<int>;
using InnerEdgeMap = std::unordered_map<State, Combination, hash_state>;
using EdgeMap = std::unordered_map<State, InnerEdgeMap, hash_state>;

static double combination_price(const Combination &combination,
                                const std::vector<Enhancement> &enhancements,
                                double book_price) {
  double total = 0.0;
  size_t num_enhancements = enhancements.size();
  size_t n = combination.size();
  for (size_t i = 0; i < n; i++) {
    int count = combination[i];
    if (i == num_enhancements) {
      total += count * book_price;
      break;
    }
    total += count * enhancements[i].price;
  }
  return total;
}

static long combination_rate(const Combination &combination,
                             const std::vector<Enhancement> &enhancements) {
  long total = 0;
  size_t num_enhancements = enhancements.size();
  size_t n = combination.size();
  for (size_t i = 0; i < n; i++) {
    int count = combination[i];
    if (i == num_enhancements) {
      total += count * BOOK_RATE;
      break;
    }
    total += count * enhancements[i].rate;
  }
  return total;
}

static void load_combination_vec(std::vector<Combination> &combinations,
                                 bool has_book, double book_price,
                                 size_t num_enhancements,
                                 size_t num_enhancements_with_book,
                                 std::vector<Enhancement> &enhancement_vec,
                                 long max_enhancement_rate) {
  // Calculate enhancement combination list

  std::vector<Combination> all_combinations;

  Combination current_combination(num_enhancements_with_book, 0);
  if (num_enhancements_with_book > 0) {
    current_combination[0] = -1;
  }

  bool carry = false;
  while (!carry) {
    carry = true;
    for (size_t i = 0; i < num_enhancements_with_book; i++) {
      int current_num = ++current_combination[i];
      if ((i < num_enhancements &&
           current_num <= enhancement_vec[i].max_amount) ||
          (i == num_enhancements && current_num <= 1)) {
        carry = false;
        all_combinations.push_back(Combination(current_combination));
        break;
      }
      current_combination[i] = 0;
    }
  }

  // Calculate prices and rates

  size_t total_combinations = all_combinations.size();
  std::vector<double> combination_price_vec(total_combinations, 0.0);
  std::vector<long> combination_rate_vec(total_combinations, 0);
  std::vector<size_t> indices;
  for (size_t i = 0; i < total_combinations; i++) {
    Combination combination = all_combinations[i];
    indices.push_back(i);
    for (size_t j = 0; j < num_enhancements_with_book; j++) {
      int count = combination[j];
      if (j == num_enhancements) {
        combination_price_vec[i] += count * book_price;
        combination_rate_vec[i] += count * BOOK_RATE;
        break;
      }
      Enhancement enhancement = enhancement_vec[j];
      combination_price_vec[i] += count * enhancement.price;
      combination_rate_vec[i] += count * enhancement.rate;
      combination_rate_vec[i] =
          std::min(combination_rate_vec[i], max_enhancement_rate);
    }
  }

  // Filter combinations for prices and rates

  std::sort(indices.begin(), indices.end(),
            [combination_rate_vec,
             combination_price_vec](const size_t &a, const size_t &b) -> bool {
              long rate_a = combination_rate_vec[a];
              long rate_b = combination_rate_vec[b];
              if (rate_a != rate_b) {
                return rate_a > rate_b;
              }
              return combination_price_vec[a] < combination_price_vec[b];
            });

  combinations.clear();
  double min_price = MAX_PRICE;
  long prev_rate = -1;
  for (size_t i : indices) {
    long rate = combination_rate_vec[i];
    if (rate == prev_rate) {
      continue;
    }
    prev_rate = rate;

    double current_price = combination_price_vec[i];
    if (min_price != MAX_PRICE && current_price >= min_price) {
      continue;
    }
    min_price = current_price;

    Combination combination = all_combinations[i];
    combinations.push_back(combination);
  }
}

static void load_graph(EdgeMap &in_edges, EdgeMap &out_edges, long base_rate,
                       long starting_rate, long starting_artisans_points,
                       size_t num_enhancements_with_book,
                       std::vector<Combination> &combinations,
                       std::vector<Enhancement> &enhancement_vec) {
  size_t num_combinations = combinations.size();
  long max_base_rate = base_rate << 1;

  State starting_state = {starting_rate, starting_artisans_points};
  Combination empty_combination = Combination(num_enhancements_with_book, 0);

  in_edges.clear();
  out_edges.clear();

  in_edges[starting_state] = InnerEdgeMap();
  in_edges[GUARANTEED_SUCCESS] = InnerEdgeMap();
  out_edges[GUARANTEED_SUCCESS] = InnerEdgeMap();

  std::vector<State> stack{starting_state};
  while (!stack.empty()) {
    State current_state = stack.back();
    stack.pop_back();
    auto found = out_edges.find(current_state);
    if (found != out_edges.end()) {
      continue;
    }
    out_edges[current_state] = InnerEdgeMap();
    if (current_state.artisans_points >= MAX_ARTISANS_POINTS) {
      out_edges[current_state][GUARANTEED_SUCCESS] = empty_combination;
      in_edges[GUARANTEED_SUCCESS][current_state] = empty_combination;
      continue;
    }
    for (size_t i = 0; i < num_combinations; i++) {
      Combination combination = combinations[num_combinations - 1 - i];
      long c_rate = combination_rate(combination, enhancement_vec);

      long success = std::min(current_state.honing_rate + c_rate, MYRIA);

      State out_state = GUARANTEED_SUCCESS;
      if (success < MYRIA) {
        long new_honing_rate =
            std::min(current_state.honing_rate + base_rate / 10, max_base_rate);
        long new_artisans_points = current_state.artisans_points + success;
        out_state = {new_honing_rate, new_artisans_points};
        stack.push_back(out_state);
      }

      auto found_inner = out_edges[current_state].find(out_state);
      if (found_inner != out_edges[current_state].end()) {
        continue;
      }
      out_edges[current_state][out_state] = combination;
      found_inner = in_edges[out_state].find(current_state);
      if (found_inner != in_edges[out_state].end()) {
        in_edges[out_state] = InnerEdgeMap();
      }
      in_edges[out_state][current_state] = combination;
    }
  }
}

static PyObject *honing_c_get_strategy(PyObject *self, PyObject *args) {
  // Get arguments
  PyObject *honing_level;
  double base_cost;
  PyObject *enhancement_price_list;
  long starting_rate, starting_artisans_points;
  if (!PyArg_ParseTuple(args, "OdOll", &honing_level, &base_cost,
                        &enhancement_price_list, &starting_rate,
                        &starting_artisans_points)) {
    return NULL;
  }

  // Load python objects into cpp objects
  PyObject *py_base_rate =
      PyObject_GetAttrString(honing_level, "base_rate_permyria");
  if (py_base_rate == NULL) {
    return NULL;
  }
  long base_rate = PyLong_AsLong(py_base_rate);
  if (base_rate == -1 && PyErr_Occurred() != NULL) {
    return NULL;
  }

  PyObject *py_book_id = PyObject_GetAttrString(honing_level, "book_id");
  if (py_book_id == NULL) {
    return NULL;
  }
  bool has_book = py_book_id != Py_None;

  PyObject *py_max_enhancement_rate =
      PyObject_GetAttrString(honing_level, "max_enhancement_rate_permyria");
  if (py_max_enhancement_rate == NULL) {
    return NULL;
  }
  long max_enhancement_rate = PyLong_AsLong(py_max_enhancement_rate);
  if (max_enhancement_rate == -1 && PyErr_Occurred() != NULL) {
    return NULL;
  }

  PyObject *py_enhancement_list =
      PyObject_GetAttrString(honing_level, "enhancements");
  if (py_enhancement_list == NULL) {
    return NULL;
  }

  Py_ssize_t py_num_enhancements = PyObject_Length(py_enhancement_list);
  if (py_num_enhancements == -1) {
    return NULL;
  }
  size_t num_enhancements = py_num_enhancements;
  std::vector<Enhancement> enhancement_vec(num_enhancements);
  for (size_t i = 0; i < num_enhancements; i++) {
    PyObject *index = Py_BuildValue("i", i);
    if (index == NULL) {
      return NULL;
    }

    PyObject *enhancement = PyObject_GetItem(py_enhancement_list, index);
    if (enhancement == NULL) {
      return NULL;
    }

    long rate_increase = PyLong_AsLong(
        PyObject_GetAttrString(enhancement, "rate_increase_permyria"));
    if (rate_increase == -1 && PyErr_Occurred() != NULL) {
      return NULL;
    }
    enhancement_vec[i].rate = rate_increase;

    long max_amount =
        PyLong_AsLong(PyObject_GetAttrString(enhancement, "max_amount"));
    if (max_amount == -1 && PyErr_Occurred() != NULL) {
      return NULL;
    }
    enhancement_vec[i].max_amount = max_amount;

    double enhancement_price =
        PyFloat_AsDouble(PyObject_GetItem(enhancement_price_list, index));
    if (enhancement_price == -1.0 && PyErr_Occurred() != NULL) {
      return NULL;
    }
    enhancement_vec[i].price = enhancement_price;
  }

  double book_price = 0.0;
  if (has_book) {
    PyObject *py_book_price =
        PyList_GetItem(enhancement_price_list, num_enhancements);
    if (py_book_price == NULL) {
      return NULL;
    }
    book_price = PyFloat_AsDouble(py_book_price);
    if (book_price == -1.0 && PyErr_Occurred() != NULL) {
      return NULL;
    }
  }

  size_t num_enhancements_with_book =
      has_book ? num_enhancements + 1 : num_enhancements;

  std::vector<Combination> combinations;
  load_combination_vec(combinations, has_book, book_price, num_enhancements,
                       num_enhancements_with_book, enhancement_vec,
                       max_enhancement_rate);

  EdgeMap in_edges, out_edges;
  load_graph(in_edges, out_edges, base_rate, starting_rate,
             starting_artisans_points, num_enhancements_with_book, combinations,
             enhancement_vec);

  // Calculate lowest price

  std::unordered_map<State, size_t, hash_state> out_edges_counts;
  for (auto &pair : out_edges) {
    out_edges_counts[pair.first] = pair.second.size();
  }
  std::vector<State> terminal_states{GUARANTEED_SUCCESS};

  std::unordered_map<State, double, hash_state> costs;
  std::unordered_map<State, std::pair<State, Combination>, hash_state>
      best_out_edge;

  while (!terminal_states.empty()) {
    State current_state = terminal_states.back();
    terminal_states.pop_back();

    double min_cost = -1;
    std::pair<State, Combination> min_edge;
    for (auto &pair : out_edges[current_state]) {
      State out_state = pair.first;
      Combination combination = pair.second;

      long c_rate = combination_rate(combination, enhancement_vec);
      long enhanced_rate = std::min(current_state.honing_rate + c_rate, MYRIA);
      double c_price =
          combination_price(combination, enhancement_vec, book_price);
      double ev = base_cost + c_price +
                  costs[out_state] * (MYRIA - enhanced_rate) / MYRIA;
      if (min_cost == -1 || ev < min_cost) {
        min_cost = ev;
        min_edge = {out_state, combination};
      }
    }

    if (min_cost == -1) {
      costs[current_state] = 0.0;
    } else {
      costs[current_state] = min_cost;
      best_out_edge[current_state] = min_edge;
    }

    for (auto &pair : in_edges[current_state]) {
      State in_state = pair.first;
      out_edges_counts[in_state] -= 1;
      if (!out_edges_counts[in_state]) {
        terminal_states.push_back(in_state);
      }
    }
  }

  // Construct return value

  PyObject *py_tuple = PyTuple_New(2);
  if (py_tuple == NULL) {
    return NULL;
  }

  PyObject *py_actions = PyList_New(0);
  if (py_actions == NULL) {
    return NULL;
  }
  if (PyTuple_SetItem(py_tuple, 0, py_actions) == -1) {
    return NULL;
  }

  PyObject *py_states = PyList_New(0);
  if (py_states == NULL) {
    return NULL;
  }
  if (PyTuple_SetItem(py_tuple, 1, py_states) == -1) {
    return NULL;
  }

  std::vector<Combination> best_actions;
  std::vector<State> best_states;
  State current_state = {starting_rate, starting_artisans_points};

  while (current_state != GUARANTEED_SUCCESS) {
    std::pair<State, Combination> p = best_out_edge[current_state];
    State next_state = p.first;
    Combination combination = p.second;

    PyObject *py_combination = PyTuple_New(num_enhancements_with_book);
    if (py_combination == NULL) {
      return NULL;
    }
    for (size_t i = 0; i < num_enhancements_with_book; i++) {
      PyObject *py_count = Py_BuildValue("i", combination[i]);
      if (py_count == NULL) {
        return NULL;
      }
      if (PyTuple_SetItem(py_combination, i, py_count) == -1) {
        return NULL;
      }
    }
    if (PyList_Append(py_actions, py_combination) == -1) {
      return NULL;
    }

    PyObject *py_state =
        PyTuple_Pack(2, Py_BuildValue("l", current_state.honing_rate),
                     Py_BuildValue("l", current_state.artisans_points));
    if (py_state == NULL) {
      return NULL;
    }
    if (PyList_Append(py_states, py_state) == -1) {
      return NULL;
    }

    current_state = next_state;
  }

  return py_tuple;
}

static PyMethodDef HoningMethods[] = {
    {"get_strategy", honing_c_get_strategy, METH_VARARGS,
     "Calculates the honing strategy."},
    {NULL, NULL, 0, NULL} // Sentinel
};

static struct PyModuleDef honingmodule = {PyModuleDef_HEAD_INIT, "honing_cpp",
                                          NULL, -1, HoningMethods};

PyMODINIT_FUNC PyInit_honing_cpp(void) {
  return PyModule_Create(&honingmodule);
}
