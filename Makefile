#
#	File: Makefile
#	

CC=gcc
PY=2.7
C_FLAGS=-fPIC -Wall -Werror -c -O3 -I/usr/include/python$(PY) -DPYTHON$(subst m,,$(subst .,,$(PY)))
L_FLAGS=-lpython$(PY) -lbluetooth -shared
OBJS=bdaddr.o oui.o btmitm_clone.o


clone.so: $(OBJS) blocksdp.so
	$(CC) $(OBJS) $(L_FLAGS) -o clone.so

blocksdp.so: blocksdp.o
	$(CC) -shared $^ -o $@

blocksdp.o: blocksdp.c
	$(CC) $^ $(C_FLAGS) -o $@


%.o: %.c
	$(CC) $(C_FLAGS) $*.c -o $@

clean:
	rm -rf *.o clone.so blocksdp.so *.log *.pyc
