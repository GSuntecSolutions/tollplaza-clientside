🖥️ Machine B (GPU): Export Image Directory via NFS:-->
1.    `sudo apt update && sudo apt install nfs-kernel-server -y ` # install nfs 
2.    `sudo mkdir -p /shared/images`    # create image directory 
3.    `sudo chown nobody:nogroup /shared/images` or `sudo chown $(whoami):$(whoami) /shared/videos`
4.    `sudo chmod 777 /shared/images`

5.   ` echo "/shared/images 101.53.132.75(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports  `  
    
6.    `sudo exportfs -a`
7.    `sudo systemctl restart nfs-kernel-server`    ## Restart NFS:


8.   `cat /etc/exports`  # check Exports Configuration.  : below output is displayed 
    /shared/videos 101.53.132.75(rw,sync,no_subtree_check)  # if shared successfuly then path should be there 
    /shared/images 101.53.132.75(rw,sync,no_subtree_check)
9.    `sudo systemctl status nfs-kernel-server`  // If not active run below commands:
                        `sudo systemctl start nfs-kernel-server`
                        `sudo systemctl enable nfs-kernel-server`



🖥️ Machine A (Next.js): Mount NFS Share
    `sudo apt install nfs-common -y`  # Install NFS client:
    `sudo mkdir -p /home/ubuntu/shared-images `  ## Create mount point:
    `sudo mount 164.52.201.243:/shared/images /home/ubuntu/shared-images`   ## mount 
    `echo "164.52.201.243:/shared/images /home/ubuntu/shared-images nfs defaults 0 0" | sudo tee -a /etc/fstab ` ### Make permanent (/etc/fstab):
    ` mkdir -p public`

    Serve Images in Next.js (Machine A): 
        cd /root/NextjsApps/firstapp
        ln -s /home/ubuntu/shared-images public/images  ### Link the mounted folder to public:


## NOTES: Verify hand sharing between two server And shorting :
    Machine B (Client side): 
1. a.        `sudo exportfs -ra`
2. b.        `sudo ufw allow from 101.53.132.75 to any port nfs` # Open Firewall for NFS 

    Machine A (GSTS side):    
3.    `ping 164.52.201.243` # # Ping GPU machine
3. a.  `nc -zv 164.52.201.243 2049`  # expected out put `Connection to 164.52.201.243 2049 port [tcp/*] succeeded!`
3. b  `sudo mkdir -p /home/ubuntu/shared-videos`  
3. c.  `sudo mount -t nfs -v 164.52.201.243:/shared/videos /home/ubuntu/shared-videos`
3. d.   `sudo mount -t nfs -o rw,hard,intr,nfsvers=4 164.52.201.243:/shared/videos /home/ubuntu/shared-videos`

