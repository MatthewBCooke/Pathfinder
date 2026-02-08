function output=Entropy(x,y,Xp,Yp) %ent_kl,E_bar;
     gal=zeros(1,1);
     LogE=zeros(1,1);
     plat_x=Xp;
     plat_y=Yp;
     Xraw=x(:);
     Yraw=y(:);
     if iscell(Xraw)
      Xraw = cell2mat(Xraw);
     end
     if iscell(Yraw)
      Yraw = cell2mat(Yraw);
     end
     d_x=Xraw-plat_x;
     d_y=Yraw-plat_y;
     Dx=d_x*1;
     Dy=d_y*1;
     dist2=(Dx.^2+Dy.^2)';
     dist=sqrt(dist2);
     dist_ave=mean(dist,2);
     gal=(dist_ave);
     w=1;
     w=w';
     sw=sum(w,1);
     xm=(mean(w.*Dx,1))./sw;
     ym=(mean(w.*Dy,1))./sw;
     xxm=(mean(w.*Dx.*Dx,1))./sw;
     yym=(mean(w.*Dy.*Dy,1))./sw;
     xym=(mean(w.*Dx.*Dy,1))./sw;
     var_xy2=0;
     Sig=zeros(2);
     eig_val=zeros(2,1);
     i=1;
       Sig=[xxm(i)-xm(i).^2, xym(i)-xm(i)*ym(i);xym(i)-xm(i)*ym(i), yym(i)-ym(i)^2];
       eig_val=eig(Sig);
       var_xy2(i)=eig_val(1)*eig_val(2);
     mdist2=mean(w'.*dist2,2)./sw';%nx1
aa=mdist2;
epsilon = 1e-10;
safe_aa = max(aa, epsilon);
safe_var_xy2 = max(var_xy2, epsilon);
LogE=2*0.5*log(safe_aa)+2*0.5*(1/2)*log(safe_var_xy2);
output = mean(LogE);
