# vmware-snapshot-taker
Triggers a snapshot for VMs listed in a file

Based on a couple of the samples in the pyvomi repo https://github.com/vmware/pyvmomi-community-samples

# Sample CLI

```
python sig-vmware-snapshot-taker.py \
       -s myvsphere.acme.com \
      -u mydomain\\dnorth    \
      -p 'my password'       \
      -S                     \
      -f snapshot_vms.json
```

-S is a toggle to enable/Disable strict SSL checking (ie. if using a self-signed cert, specify -S; if using a "real" cert, omit -S)
