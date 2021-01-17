/*
 * Copyright (C) 2018 Joseph Heled.
 * Copyright (c) 2019-2021 Matthew Sheby.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#define PY_SSIZE_T_CLEAN 1
#undef NDEBUG
#include <Python.h>
#if PY_MAJOR_VERSION >= 3
#define PyInt_AsLong PyLong_AsLong
#define PyInt_FromLong PyLong_FromLong
#endif

static int bmap[20][20];

static int
binomial(const int n, const int k)
{
  if( n < k )  return 0;
  if( k == 0 || n == k ) return 1;
  return binomial(n-1,k) + binomial(n-1,k-1);
}

static void
initm(void)
{
  int n, k;
  for(n = 0; n < 20; ++n) {
    for(k = 0; k < 20; ++k) {
      bmap[n][k] = binomial(n,k);
    }
  }
}

static int
sum(int const a[], unsigned int const n)
{
  int s = 0;
  unsigned int k;
  for(k = 0; k < n; ++ k) {
    s += a[k];
  }
  return s;
}

static unsigned int
bitsIndex(int const bits[], int k, unsigned int const N)
{
  int i = 0, n = N;
  unsigned int j;
  for(j = 0; j < N; ++j) {
    if( bits[j] ) {
      i += bmap[n-1][k];
      k -= 1;
    }
    n -= 1;
  }
  return i;
}

static void
i2bits(int bits[], unsigned int i, int k, int N)
{
  int j;
  unsigned int bnk;
  for(j = 0; j < N; ++j) {
    bits[j] = 0;
  }
  j = 0;
  while( N > 0 ) {
    bnk = bmap[N-1][k];
    if( i >= bnk ) {
      bits[j] = 1;
      i -= bnk;
      k -= 1;
    }
    N -= 1;
    j += 1;
  }
}

static const unsigned int GR_OFF = 14;
static const unsigned int RD_OFF = 21;


static PyObject*
board2Index(PyObject* module, PyObject* args)
{
  PyObject* pyBoard;
  PyObject* spMap;
  PyObject* pSums;
  PyObject* pyi0;
  PyObject** s;
  PyObject* t;
  PyObject* pyps;
  long i0, i1, i2, i3;
  unsigned int m, k, nb;
  int b[22];
  int bits[14];
  int gSafe[6];
  int gOff, rOff, gHome, rHome, smb, gStrip, partSafeG, gMen, rMen, partR;

  if( !PyArg_ParseTuple(args, "OOO", &pyBoard, &spMap, &pSums) ) {
    PyErr_SetString(PyExc_ValueError, "wrong args.");
    return 0;
  }

  if( !(PySequence_Check(pyBoard) && PySequence_Size(pyBoard) == 22) ) {
    PyErr_SetString(PyExc_ValueError, "wrong args.");
    return 0;
  }

  if( !( PyDict_Check(spMap) && PyDict_Check(pSums) ) ) {
    PyErr_SetString(PyExc_ValueError, "wrong args.");
    return 0;
  }

  s = &PyList_GET_ITEM(pyBoard, 0);
  for(k = 0; k < 22; ++k) {
    b[k] = PyInt_AsLong(s[k]);
  }

  gOff = b[GR_OFF];
  rOff = b[RD_OFF];

  gSafe[0] = b[0];gSafe[1] = b[1];gSafe[2] = b[2];gSafe[3] = b[3];gSafe[4] = b[12];gSafe[5] = b[13];
  m = sum(gSafe, 6);
  partSafeG = bitsIndex(gSafe, m, 6);
  for(k = 4; k < 12; ++k) {
    bits[k-4] = b[k] == 1;
  }
  smb = sum(bits, 8);
  gStrip = bitsIndex(bits, smb, 8);
  gMen = smb + m;

  for(k = 15; k < 19; ++k) {
    bits[k-15] = b[k] == -1;
  }

  nb = 4;
  for(k = 4; k < 12; ++k) {
    if( b[k] == 1 ) {
      continue;
    }
    bits[nb] = b[k] == -1;
    nb += 1;
  }
  for(k = 19; k < 21; ++k, ++nb) {
    bits[nb] = b[k] == -1;
  }
  rMen = sum(bits, nb);
  partR = bitsIndex(bits, rMen, nb);

  gHome = 7 - (gMen + gOff);
  rHome = 7 - (rMen + rOff);

  t = PyTuple_New(4);
  PyTuple_SET_ITEM(t, 0, PyLong_FromLong(gOff));
  PyTuple_SET_ITEM(t, 1, PyLong_FromLong(rOff));
  PyTuple_SET_ITEM(t, 2, PyLong_FromLong(gHome));
  PyTuple_SET_ITEM(t, 3, PyLong_FromLong(rHome));

  pyi0 = PyDict_GetItem(spMap, t);
  Py_DECREF(t);

  if( ! pyi0 ) {
    PyErr_SetString(PyExc_ValueError, "wrong args.");
    return 0;
  }

  i0 = PyLong_AsLong(pyi0);

  t = PyTuple_New(2);
  PyTuple_SET_ITEM(t, 0, PyLong_FromLong(gMen));
  PyTuple_SET_ITEM(t, 1, PyLong_FromLong(rMen));

  pyps = PyDict_GetItem(pSums, t);     assert(pyps);
  Py_DECREF(t);

  if( ! PySequence_Check(pyps) ) {
    Py_INCREF(Py_None);
    return Py_None;
  }
  i1 = PyLong_AsLong(PyList_GET_ITEM(pyps, m));
  i2 = partSafeG * bmap[8][gMen - m] + gStrip;
  i3 = i2 * bmap[14 - (gMen-m)][rMen] + partR;

  return PyLong_FromLong(i0 + i1 + i3);
}

static PyObject*
index2Board(PyObject* module, PyObject* args)
{
  PyObject *pi, *a0, *a1, *a2, *a3;
  PyObject *pSums;
  PyObject* pyb;
  PyObject* t;
  PyObject* pyps;
  PyObject** ps;
  Py_ssize_t plen;
  long index, gOff, rOff, gHome, rHome, gMen, rMen;
  unsigned int u, i2, partR, partSafeG, gStrip;
  int b[22] = {0};
  int bOther[14];
  int m = 0;
  int i, k;

  if( !PyArg_ParseTuple(args, "OOOOOO", &pi, &a0, &a1, &a2, &a3, &pSums) ) {
    PyErr_SetString(PyExc_ValueError, "wrong args.");
    return 0;
  }
  index = PyLong_AsLong(pi);
  gOff = PyLong_AsLong(a0);
  rOff = PyLong_AsLong(a1);
  gHome = PyLong_AsLong(a2);
  rHome = PyLong_AsLong(a3);

  gMen = 7 - (gOff + gHome);
  rMen = 7 - (rOff + rHome);
  t = PyTuple_New(2);
  PyTuple_SET_ITEM(t, 0, PyLong_FromLong(gMen));
  PyTuple_SET_ITEM(t, 1, PyLong_FromLong(rMen));

  pyps = PyDict_GetItem(pSums, t);     assert(pyps && PySequence_Check(pyps));
  Py_DECREF(t);

  plen = PySequence_Length(pyps);

  ps = &PyList_GET_ITEM(pyps, 0);
  if( index >= PyLong_AsLong(ps[plen-1]) ) {
    PyErr_SetString(PyExc_ValueError, "Index invalid");
    return 0;
  }

  while( ! ( PyLong_AsLong(ps[m]) <= index && index < PyLong_AsLong(ps[m+1]) ) ) {
    m += 1;
  }
  index -= PyLong_AsLong(ps[m]);

  u = bmap[14 - (gMen-m)][rMen];
  i2 = index / u;
  partR = index - i2 * u;
  u = bmap[8][gMen - m];
  partSafeG = i2 / u;
  gStrip = i2 - u * partSafeG;

  b[14] = gOff;
  b[21] = rOff;

  i2bits(b, partSafeG, m ,6);
  b[12] = b[4];
  b[13] = b[5];
  b[4] = b[5] = 0;

  i2bits(b + 4, gStrip, gMen - m, 8);

  i2bits(bOther, partR, rMen, 14 - (gMen-m));

  for(i = 0; i < 4; ++i) {
    b[15+i] = -bOther[i];
  }
  for(k = 4; k < 12; ++k) {
    if( b[k] == 0 ) {
      if( bOther[i] ) {
	      b[k] = -1;
      }
      i += 1;
    }
  }
  b[19] = -bOther[i];
  b[20] = -bOther[i+1];

  pyb = PyList_New(22);
  for(i = 0; i < 22; ++i) {
    PyList_SET_ITEM(pyb, i, PyLong_FromLong(b[i]));
  }
  return pyb;
}

static PyMethodDef irMethods[] =
{
  {"board2Index", board2Index, METH_VARARGS, ""},

  {"index2Board", index2Board, METH_VARARGS, ""},

  {NULL, NULL, 0, NULL}        /* Sentinel */
};

#if PY_MAJOR_VERSION >= 3
    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "irogaur",           /* m_name */
        NULL,                /* m_doc */
        -1,                  /* m_size */
        irMethods,           /* m_methods */
        NULL,                /* m_reload */
        NULL,                /* m_traverse */
        NULL,                /* m_clear */
        NULL,                /* m_free */
    };
#endif

PyMODINIT_FUNC
#if PY_MAJOR_VERSION >= 3
PyInit_irogaur(void)
#else
initirogaur(void)
#endif
{
  PyObject *m = NULL;
  initm();
#if PY_MAJOR_VERSION >= 3
  m = PyModule_Create(&moduledef);
#else
  m = Py_InitModule("irogaur", irMethods);
#endif

#if PY_MAJOR_VERSION >= 3
  return m;
#else
  return;
#endif
}
