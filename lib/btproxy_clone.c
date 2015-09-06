/*
  Date: Jun 24 2015
  Source File: btproxy_clone.c

  Interface to setting attributes on a Bluetooth card
  for the python program.
*/
#include <stdio.h>
#include <Python.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>

extern int c_set_adapter_address(int,char*);

static void * die(const char* msg)
{
    PyErr_SetString(PyExc_RuntimeError, msg);
    return NULL;
}

/* 
*/
__attribute__((unused))
static PyObject* py_set_adapter_name(PyObject* self, PyObject* args)
{

	int dd,hdev;
    char* name;

    PyArg_ParseTuple(args, "is", &hdev, &name);

	dd = hci_open_dev(hdev);
	if (dd < 0) {
        char buf[300];
		snprintf(buf, sizeof buf, "Can't open device hci%d: %s (%d)\n",
						hdev, strerror(errno), errno);
		return die(buf);
	}

	if (name) {
		if (hci_write_local_name(dd, name, 2000) < 0) {
            char buf[300];
			snprintf(buf, sizeof buf, "Can't change local name on hci%d: %s (%d)\n",
						hdev, strerror(errno), errno);
		    return die(buf);
		}
	}
    else
    {
		return die("No name given\n");
    }
	
	hci_close_dev(dd);
	return Py_BuildValue("s",name);
}


__attribute__((unused))
static PyObject* py_set_adapter_address(PyObject* self, PyObject* args)
{
    int dev;
    char* new_addr;
    PyArg_ParseTuple(args, "is", &dev, &new_addr);
    int ret = c_set_adapter_address(dev,new_addr);
    if (ret != 0)
    {
        return NULL;
    }
	return Py_BuildValue("s",new_addr);
}


/* 
*/
__attribute__((unused))
static PyObject* py_set_adapter_class(PyObject* self, PyObject* args)
{
    int hdev;
    char* class;

    PyArg_ParseTuple(args, "is", &hdev, &class);
	
	int s = hci_open_dev(hdev);
	if (s < 0) {
        char buf[300];
		snprintf(buf, sizeof buf,"Can't open device hci%d: %s (%d)\n",
						hdev, strerror(errno), errno);
        return die(buf);

	}
	if (class) {
		uint32_t cod = strtoul(class, NULL, 16);
		if (hci_write_class_of_dev(s, cod, 2000) < 0) {
            char buf[300];
			snprintf(buf, sizeof buf,"Can't write local class of device on hci%d: %s (%d)\n",
						hdev, strerror(errno), errno);
            return die(buf);
		 }
	}
    else
    {
        fprintf(stderr, "no class given\n");
    }
    return Py_BuildValue("s",class);
}


/*  Bind Python names to c names
 * */
static PyMethodDef py_module_methods[] = {
    {"set_adapter_name", py_set_adapter_name, METH_VARARGS},
    {"set_adapter_class", py_set_adapter_class, METH_VARARGS},
    {"set_adapter_address", py_set_adapter_address, METH_VARARGS},
    {NULL, NULL}
};

#if defined PYTHON34 || defined PYTHON340
static struct PyModuleDef clone_module = {
    PyModuleDef_HEAD_INIT,
    "clone",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* -1 if the module keeps state in global variables. */
    py_module_methods, /* Method table */
};

PyMODINIT_FUNC
PyInit_clone(void)
{
    return PyModule_Create(&clone_module);
}
#else
// Called by python first
void initclone(void)
{
    (void) Py_InitModule("clone", py_module_methods);
}
#endif



