#
#	File: Makefile
#	

CC=gcc
PY=2.7
C_FLAGS=-fPIC -Wall -Werror -c -O3 -I/usr/include/python$(PY) -DPYTHON$(subst m,,$(subst .,,$(PY)))
L_FLAGS=-lpython$(PY) -lbluetooth -shared
OBJS_=bdaddr.o oui.o btmitm_clone.o
LIB=lib
OBJS=$(addprefix $(LIB)/, $(OBJS_))

clone.so: $(OBJS) blocksdp.so
	$(CC) $(OBJS) $(L_FLAGS) -o clone.so

blocksdp.so: $(LIB)/blocksdp.o
	$(CC) -shared $^ -o $@

blocksdp.o: $(LIB)/blocksdp.c
	$(CC) $< $(C_FLAGS) -o $(LIB)/$@

%.o: %.c
	$(CC) $(C_FLAGS) $< -o $@

install:
	chmod +x scripts/*
	ln -s $(shell pwd)/scripts/replace_bluetoothd.bash /usr/local/bin/replace_bluetoothd
	ln -s $(shell pwd)/btmitm/btmitm.py /usr/local/bin/btmitm

clean:
	rm -rf $(LIB)/*.o clone.so blocksdp.so *.log *.pyc
