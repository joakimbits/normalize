# greeting on stdout
.global _start
.text
_start:
    # write(1, msg, 21)
    mov     $1, %rax    # system call 1 is write
    mov     $1, %rdi    # file handle 1 is stdout
    mov     $msg, %rsi  # address of string to output
    mov     $21, %rdx   # number of bytes to output
    syscall             # invoke operating system to do the write

    # main()
    call    main

    # exit(0)
    mov     $60, %rax   # system call 60 is exit
    xor     %rdi, %rdi  # return code 0 is no error
    syscall             # invoke operating system to exit
msg:
    .ascii  "Hello from _start.s!\n"

