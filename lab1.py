ip_address=input("enter ip address: ")
subnet_mask=input("enter subnet mask: ")
legal=0
ip_list=ip_address.split('.')
mask_list=subnet_mask.split('.')
for num1 in ip_list:
    if int(num1)>255:
        print('ip address illegal')
        legal=1
        break
for num2 in mask_list:
    if int(num2)>255:
        print('subnet mask illegal')
        legal=1
        break
p=0
for num2 in mask_list:
    if int(num2)<255:
        if p==0:
            p=1
        else:
            print('subnet mask illegal')
            legal=1
if legal==0:
    network_list=[0,0,0,0]
    host_list=[0,0,0,0]
    for i in range(0,4):
        network_list[i]=str(int(ip_list[i])&int(mask_list[i]))
        host_list[i]=str(int(ip_list[i])&(~int(mask_list[i])))
    network_id='.'.join(network_list)
    host_id=''
    for num in host_list:
        if num!='0':
            host_id=host_id+str(num)
    print('network_id= ',network_id)
    print('host_id= ',host_id)




