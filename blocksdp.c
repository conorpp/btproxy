/*
 * Use this to block SDP PSM  from being binded to
 * from another program (like bluetoothd)
 *
 * e.g. .LD_PRELOAD=./blocksdp.so bluetoothd -n
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/l2cap.h>
#include <bluetooth/rfcomm.h>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

int (*_bind)(int, const struct sockaddr *, socklen_t);

static int isValidChannel(int p)
{
    return (p>0 && p<31);
}
static int isValidPSM(int p)
{
    return (p % 2 == 1 && p > 0 && p < 32766);
}

static int unlock = 0;

uint32_t btmitm = -1;

static void alarmcb(int sig)
{
    unlock = 1;
}

int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen)
{
    if (btmitm == -1)
    {
        signal(SIGALRM, alarmcb);
        if ( alarm(3) < 0)
        {
            perror("alarm");
            exit(1);
        }
        _bind = (int (*)(int, const struct sockaddr *, socklen_t)) dlsym(RTLD_NEXT, "bind");
    }
    struct sockaddr_l2* l2 = (struct sockaddr_l2*)addr;
    struct sockaddr_rc* rc = (struct sockaddr_rc*)addr;

    printf("psm: %d or channel: %d\n", l2->l2_psm, rc->rc_channel);

    if (unlock)
    {
        return _bind(sockfd, addr, addrlen);
    }


    // Nope, all RFCOMM is mine
    if (isValidChannel( rc->rc_channel ))
    {
/*
        fprintf(stderr,"Blocked rfcomm channel %d\n", rc->rc_channel);
        return -1;
*/
    }

    if (l2->l2_psm == 1){
        l2->l2_psm = l2->l2_psm + 100;
        fprintf(stderr, "Moved system SDP PSM 1 to %d so its up for grabs.\n", l2->l2_psm);
        return _bind(sockfd, addr, addrlen);
    }
    if (isValidPSM(l2->l2_psm) && l2->l2_psm < 4096)
    {
/*
        fprintf(stderr,"Blocked l2cap psm %d\n", l2->l2_psm);
        return -1;
*/
    }
    return _bind(sockfd, addr, addrlen);

}
