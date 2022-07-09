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
using InnerEdgeMap = std::unordered_map<State, size_t, hash_state>;
using EdgeMap = std::unordered_map<State, InnerEdgeMap, hash_state>;

static void load_combination_vec(std::vector<Combination> &combinations,
                                 std::vector<double> &prices,
                                 std::vector<long> &rates, bool has_book,
                                 double book_price, size_t num_enhancements,
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
  std::vector<double> all_prices(total_combinations, 0.0);
  std::vector<long> all_rates(total_combinations, 0);
  std::vector<size_t> indices;
  for (size_t i = 0; i < total_combinations; i++) {
    Combination combination = all_combinations[i];
    indices.push_back(i);
    for (size_t j = 0; j < num_enhancements_with_book; j++) {
      int count = combination[j];
      if (j == num_enhancements) {
        all_prices[i] += count * book_price;
        all_rates[i] += count * BOOK_RATE;
        break;
      }
      Enhancement enhancement = enhancement_vec[j];
      all_prices[i] += count * enhancement.price;
      all_rates[i] += count * enhancement.rate;
      all_rates[i] = std::min(all_rates[i], max_enhancement_rate);
    }
  }

  // Filter combinations for prices and rates

  std::sort(indices.begin(), indices.end(),
            [all_rates, all_prices](const size_t &a, const size_t &b) -> bool {
              long rate_a = all_rates[a];
              long rate_b = all_rates[b];
              if (rate_a != rate_b) {
                return rate_a > rate_b;
              }
              return all_prices[a] < all_prices[b];
            });

  combinations.clear();
  prices.clear();
  rates.clear();
  double min_price = MAX_PRICE;
  long prev_rate = -1;
  for (size_t i : indices) {
    long rate = all_rates[i];
    if (rate == prev_rate) {
      continue;
    }
    prev_rate = rate;

    double current_price = all_prices[i];
    if (min_price != MAX_PRICE && current_price >= min_price) {
      continue;
    }
    min_price = current_price;

    combinations.push_back(all_combinations[i]);
    prices.push_back(all_prices[i]);
    rates.push_back(all_rates[i]);
  }
}

static void load_graph(EdgeMap &in_edges, EdgeMap &out_edges, long base_rate,
                       long starting_rate, long starting_artisans_points,
                       long research_bonus, size_t num_enhancements_with_book,
                       const std::vector<long> &rates) {
  size_t num_combinations = rates.size();
  long max_base_rate = (base_rate << 1) + research_bonus;

  State starting_state = {starting_rate, starting_artisans_points};
  size_t empty_combination_index = num_combinations - 1;

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
      out_edges[current_state][GUARANTEED_SUCCESS] = empty_combination_index;
      in_edges[GUARANTEED_SUCCESS][current_state] = empty_combination_index;
      continue;
    }
    for (size_t i = 0; i < num_combinations; i++) {
      size_t combination_index = num_combinations - 1 - i;
      long c_rate = rates[combination_index];

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
      out_edges[current_state][out_state] = combination_index;
      found_inner = in_edges[out_state].find(current_state);
      if (found_inner != in_edges[out_state].end()) {
        in_edges[out_state] = InnerEdgeMap();
      }
      in_edges[out_state][current_state] = combination_index;
    }
  }
}

static PyObject *honing_c_get_strategy(PyObject *self, PyObject *args) {
  // Get arguments
  PyObject *honing_level;
  double base_cost;
  PyObject *enhancement_price_list;
  long starting_rate, starting_artisans_points;
  int researched;
  if (!PyArg_ParseTuple(args, "OdOlpl", &honing_level, &base_cost,
                        &enhancement_price_list, &starting_rate, &researched,
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

  long research_bonus = 0;
  if (researched) {
    PyObject *py_research_bonus =
        PyObject_GetAttrString(honing_level, "research_bonus_permyria");
    if (py_research_bonus == NULL) {
      return NULL;
    }
    research_bonus = PyLong_AsLong(py_research_bonus);
    if (research_bonus == -1 && PyErr_Occurred() != NULL) {
      return NULL;
    }
  }
  starting_rate += research_bonus;

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
  max_enhancement_rate = std::min(max_enhancement_rate, MYRIA - starting_rate);

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
  std::vector<double> prices;
  std::vector<long> rates;
  load_combination_vec(combinations, prices, rates, has_book, book_price,
                       num_enhancements, num_enhancements_with_book,
                       enhancement_vec, max_enhancement_rate);

  EdgeMap in_edges, out_edges;
  load_graph(in_edges, out_edges, base_rate, starting_rate,
             starting_artisans_points, research_bonus,
             num_enhancements_with_book, rates);

  // Calculate lowest price

  std::unordered_map<State, size_t, hash_state> out_edges_counts;
  for (auto &pair : out_edges) {
    out_edges_counts[pair.first] = pair.second.size();
  }
  std::vector<State> terminal_states{GUARANTEED_SUCCESS};

  std::unordered_map<State, double, hash_state> costs;
  std::unordered_map<State, std::pair<State, size_t>, hash_state> best_out_edge;

  while (!terminal_states.empty()) {
    State current_state = terminal_states.back();
    terminal_states.pop_back();

    double min_cost = -1;
    std::pair<State, size_t> min_edge;
    for (auto &pair : out_edges[current_state]) {
      State out_state = pair.first;
      size_t combination_index = pair.second;

      long c_rate = rates[combination_index];
      long enhanced_rate = std::min(current_state.honing_rate + c_rate, MYRIA);
      double c_price = prices[combination_index];
      double ev = base_cost + c_price +
                  costs[out_state] * (MYRIA - enhanced_rate) / MYRIA;
      if (min_cost == -1 || ev < min_cost) {
        min_cost = ev;
        min_edge = {out_state, combination_index};
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

  State current_state = {starting_rate, starting_artisans_points};

  while (current_state != GUARANTEED_SUCCESS) {
    std::pair<State, size_t> p = best_out_edge[current_state];
    State next_state = p.first;
    Combination combination = combinations[p.second];

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
