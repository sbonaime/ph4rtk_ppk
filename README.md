Tools to calculate DJI Phantom 4 RTK (PH4RTK) PPK positions.
> [!WARNING]
> Offset of the antenna phase center to camera CMOS center is not yet used. Next release will use this data


More tools will come

## rinex_to_ppk
Extract PPK positions using Rinex file from RTKPOST and Timestamp.MRK from PH4RTK to csv file. [OpenDroneMap](https://opendronemap.org/) option available

- Usage examples
 :
```python3 rinex_to_ppk.py -r 100_0138_Rinex.pos -t 100_0138_Timestamp.MRK -o ```


