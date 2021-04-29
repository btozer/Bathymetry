#!/usr/bin/env bash

R="-R-18/-16/17.5/21.5"

gmt begin tmp_fig png A+s0.1p+p2p E720

    gmt grdimage ${R} -JM10c SRTM15+V2.1-bs.nc -CSRTM15+V2.1.cpt -Ia315+nt0.9 -Bxa1 -Bya1
    gmt grdcut SRTM15+V2.1-bs.nc ${R} -GSRTM15+V2.1_for_ron.nc=ni

    gmt grdcut SID_MASK_V2.1-bm.nc ${R} -Gcut.nc
    gmt grdmath cut.nc 0 NAN = SID_MASK_V2.1_for_ron.nc=ni

    gmt grdimage SID_MASK_V2.1_for_ron.nc -CSID_MASK.cpt -t30 -Q

    gmt grdmath SRTM15+V2.1_for_ron.nc SID_MASK_V2.1_for_ron.nc MUL = masked_for_ron.nc=ni

    gmt grd2xyz masked_for_ron.nc -s > masked_for_ron.xyz
gmt end show
