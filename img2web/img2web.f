      program img2web
c
c  program to extract a sub array from an integer*2 Mercator grid
c
      common /grid/nlt,nln,dlt,dln,iproj
      common /bounds/rlt0,rltf,rln0,rlnf,rlnm
      character*80 filein,cs,cn,ce,cw,cscale
      integer*2 iin(21600) 
c
c  setup the grid parameters
c
      nln=21600
      nlt=17280
      rlt0=-80.738
      rln0=0.
      dln=0.016666666
      dlt=0.
      rland=998.
      rdum=999.
      iproj=2
c
c   get values from command line
c
      narg = iargc()
      if(narg.ne.6) then
 100    write(*,'(a)')
     &  'Usage: img2web filein S N W E scale > data.xyz '
        write(*,'(a)')
     &  ' '
        write(*,'(a)')
     &  ' extracts data from global grid '
        write(*,'(a)')
     &  ' scale factor (0.1-gravity) (1-topo) (0.01-geoid) '
        stop
      else
        call getarg(1,filein)
        call getarg(2,cs)
        call getarg(3,cn)
        call getarg(4,ce)
        call getarg(5,cw)
        call getarg(6,cscale)
      endif
c
c  open the file
c
      nc=index(filein,' ')
      filein(nc:nc)=char(0)
      call getfil(4,lu,filein,istat)
c
c  convert characters to numbers
c
      read(cs,*)slt0
      read(cn,*)sltf
      read(ce,*)sln0
      read(cw,*)slnf
      if(slt0.ge.sltf.or.sln0.ge.slnf) then
        write(*,'(a)')' error '
        write(*,'(a)')' S < N  and W < E '
        write(*,'(a)')'       '
        go to 100
      endif
c
c  get the scale factor
c
      read(cscale,*)scale
      ihit=0
c
c   compute the starting and ending indices
c
      call mercator(sltf,sln0,i00,j00,1)
      call mercator(slt0,slnf,iff,jff,1)
c
c  make sure the corners are within the box
c
      if(i00.eq.-1)i00=1
      if(iff.eq.-1)iff=nlt
      if(j00.eq.-1)j00=1
      if(jff.eq.-1)jff=nln
      if(j00.gt.jff)j00=1
      njout=jff-j00+1
      niout=iff-i00+1
c
c jump to the correct row
c
      ntot=0
      call podiscb(lu,1,2*nln*(i00-1))
      do 200 i=i00,iff
      call rddiscb(lu,iin,2*nln,istat)
      call swap16(iin,nln)
      if(istat.lt.0) then
        write(*,'(a)')' Problem reading input file '
        stop
      endif
      if(i.ge.i00.and.i.le.iff) then
      do 150 j=j00,jff
c
c  skip empty cells
c
      idat=iin(j)
      itest=abs(mod(idat,2))
      if(ihit.eq.1.and.itest.eq.0) go to 150
      call mercator(rltt,rlnt,i,j,-1)
c     grav=(idat-itest)*scale
      grav=idat*scale
c
c  write out latitude, longitude, and gravity anomaly (mgal) or depth
c
      ntot=ntot+1
      if(rln.gt.180.) rln=rln-360.
      write(*,901)rlnt,rltt,grav
  901 format(f9.4,f9.4,f10.2)
  150 continue
      endif
 200  continue
      call frefil(2,lu,istat)
      stop
      end
c
      subroutine mercator(rlt,rln,i,j,icall)
c
c  routine to compute the indices i,j associated with the
c  mercator projection of rlt,rln.
c
c  input
c   rlt   -   latitude (deg)
c   rln   -   longitude (deg)
c   icall -   0-set up grid parameters
c             1-calculate index i, j from rlt, rln
c            -1-calculate rlt, rln from index i, j
c
c output
c   i     -   row of matrix for rlt
c   j     -   column of matrix for rln 
c
      common /grid/nlt,nln,dlt,dln,iproj
      common /bounds/rlt0,rltf,rln0,rlnf,rlnm
      common /info/lcrt(2),lin(10),nin,lout(10),nout
      data rad /.0174533/
      save arg,rad
c
c  if icall equals 0 then get location parameters
c
      if(icall.eq.0) then
      write(lcrt(2),900)
  900 format(' # of lat, # of lon (both even): ',$)
      read(lcrt(1),*)nlt,nln
      write(lcrt(2),901)
  901 format(' minimum latitude: ',$)
      read(lcrt(1),*)rlt0
      write(lcrt(2),902)
  902 format(' minimum longitude, long. spacing (deg): ',$)
      read(lcrt(1),*)rln0,dln
      rlnf=rln0+dln*nln
c
c  check to see if the left side of the box is negative
c  and add 360. if it's true.
c
      if(rln0.lt.0.) then
      rln0=rln0+360.
      rlnf=rlnf+360.
      endif
c
c  compute the maximum latitude
c
      arg=alog(tan(rad*(45.+rlt0/2.)))
      arg2=rad*dln*nlt+arg
      term=exp(arg2)
      rltf=2.*atan(term)/rad-90.
c
c  print corners of area
c
      write(lcrt(2),903)
 903  format('  corners of area  ')
      write(lcrt(2),904)rltf,rln0,rltf,rlnf
      write(lcrt(2),904)rlt0,rln0,rlt0,rlnf
  904 format(2f9.4,6x,2f9.4)
      write(lcrt(2),905)
  905 format(' continue?  1-yes  0-no: ',$)
      read(lcrt(1),*)iyes
      if(iyes.eq.0)stop
      return
      endif
c
c compute the indices of the point
c
      if(icall.eq.1) then
        rln1=rln
        arg1=alog(tan(rad*(45.+rlt0/2.)))
        arg2=alog(tan(rad*(45.+rlt/2.)))
        i=nlt+1-(arg2-arg1)/(dln*rad)
        if(i.lt.1.or.i.gt.nlt) i=-1
  20    continue
        j=(rln1-rln0)/dln+1
        j2=j
c
c  check to see if the point lies to the left of the box
c
        if(j2.lt.1) then
        rln1=rln1+360.
        if(rln1.le.rlnf)go to 20
        endif
        if(j.lt.1.or.j.gt.nln) j=-1
      else
c
c  compute latitude and longitude
c
        if(i.lt.1.or.i.gt.nlt) then
        rlt=-999.
        return
        endif
        if(j.lt.1.or.j.gt.nln) then
        rln=-999.
        return
        endif
        arg1=rad*dln*(nlt-i+.5)
        arg2=alog(tan(rad*(45.+rlt0/2.)))
        term=exp(arg1+arg2)
        rlt=2.*atan(term)/rad-90.
        rln=rln0+dln*(j-.5)
      endif
      return
      end
c
      subroutine swap16(buf,n)        
c     f77 swap16 swaps the 2 bytes within each 16 bit word of array buf.
c  this routine is useful for converting dec 16 bit integers to other computer
c  integer formats (or vice versa).
c
c  arguments:
c     buf - the array to be converted.
c     n   - the number of 16 bit words to be converted.   integer*4
c
c  copyright: paul henkart, scripps institution of oceanography, 11 april 1982
c
      character*1 buf(1),a
c
      j=1
      do 200 i=1,n
      a=buf(j)
      buf(j)=buf(j+1)
      buf(j+1)=a
      j=j+2
  200 continue
      return
      end
