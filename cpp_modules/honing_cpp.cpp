#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *honing_c_identity(PyObject *self, PyObject *args) {
  PyObject *input;
  if (!PyArg_ParseTuple(args, "O", &input)) {
    return NULL;
  }

  return input;
}

static PyObject *honing_c_zero(PyObject *self, PyObject *args) {
  if (!PyArg_ParseTuple(args, "")) {
    return NULL;
  }

  return Py_BuildValue("i", 0);
}

static PyMethodDef HoningMethods[] = {
    {"identity", honing_c_identity, METH_VARARGS, "Returns the input value."},
    {"zero", honing_c_zero, METH_VARARGS, "Returns zero as an integer."},
    {NULL, NULL, 0, NULL} // Sentinel
};

static struct PyModuleDef honingmodule = {PyModuleDef_HEAD_INIT, "honing_cpp",
                                          NULL, -1, HoningMethods};

PyMODINIT_FUNC PyInit_honing_cpp(void) {
  return PyModule_Create(&honingmodule);
}