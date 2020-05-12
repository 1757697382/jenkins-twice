while 1:
    N = []
    B = []
    n = input().split()

    for i in input().split():
        N.append(i)
    print(N)
    for i in N:
        B.append(bin(int(i)))
    print(B)
    for i in range(0,len(B)):
        for j in range(i,len(B)):
            if B[i] & B[j] ==0:
                print(-1)
            else:
                print((0))


































































'''
while 1:
    A = []
    A1 = []
    B = []
    C = []
    D = []
    D1 = []
    D2 = []
    min = 0
    max = 0
    num = 0
    num1 = 0
    m,n = input().split()
    m = int(m)
    n = int(n)
    for i in input().split():
       A.append(int(i))
    for i in range(0,n):
        a = input()
        B.append((a))
    A = sorted(A)
    A1 = sorted(A,reverse=True)
    C = set(B)
    for i in B:
        D.append(B.count(i))
    D = sorted(D)
  #  print(A,B,C,D)
    for i in D:
        if i == 1:
            num = num+1
    D1 = D[0:num]
    D2 = D[-num+1:]
    if len(D) == num:
        for i in range(0,num):
            min = min + A[i]
            max = max + A1[i]
    else:
        min = A[0]*D2[0]
        max = A1[0]*D2[0]
        for i in range(1,len(D1)+1):
            min = min+A[i]
            max = max + A1[i]
    print(min,max)
'''