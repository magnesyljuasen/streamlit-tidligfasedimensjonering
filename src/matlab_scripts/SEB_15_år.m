% SEB Green Energy fund

clc
clear all
close all
pkg load financial

%Økonomiske betingelser.
Rente = 3.75;
Inflasjon=2;
Rente_Swapp_5=2.25;
Rentemarginal=1.5;
Rentekost=3.75;
Belaning=0.30;
Ekonomisklevetid=15;
Managementfee=1;
Bolagsskatt=22;
AsplanViak_varme=20;  %  20% av entreprenaden til Asplan Viak
AsplanViak_sol=10;    %  10% av entreprenaden til Asplan Viak
Enova=1600;           %  1600 NOK / kWh
%Investering

EffektVP=200; % installert varmeeffekt (kW)
Levert_Varmne=900000; % levert varmebehov fra VP kWh
COP=3.5;
EL_VP=Levert_Varmne/COP;
elpris=1;   % NOK / kWh  inkl alt uten mva

Boring=4.83*10^6;
VP=4*10^6;
Enova_bidrag=Enova*EffektVP;
Sol=0;

Investering=(Boring+VP-Enova_bidrag)*(1+AsplanViak_varme/100)+Sol*(1+AsplanViak_sol/100);

Driftskostnad=50000;

Eget_kap=(1-Belaning)*Investering;

Lan=Investering-Eget_kap;
Resterende_Lan=Lan;

Leasing=0.102*Investering;

Year=[0:15];

for i=1:Year(end)

%P&L

Yearly_fee(i)=Leasing*(1+Inflasjon/100).^Year(i);
Management(i)=-Investering*Managementfee/100;
Avskrivning(i)=-Investering/Ekonomisklevetid;
Yearly_drift(i)=-Driftskostnad*(1+Inflasjon/100).^Year(i);

EBIT(i)=Yearly_fee(i)+Management(i)+Avskrivning(i)+Yearly_drift(i);
Rentekostnad(i)=-Resterende_Lan*(Rentekost/100);
EBT(i)=EBIT(i)+Rentekostnad(i);
Yearly_Bolagsskatt(i)=min([0,-EBT(i)*Bolagsskatt/100]);
Vinst_etter_skatt(i)=EBT(i)+Yearly_Bolagsskatt(i);

 if i <= Ekonomisklevetid
  Ammortering(i)=-Lan/Ekonomisklevetid;
  else
  Ammortering(i)=0
  end
  Resterende_Lan=Lan+sum(Ammortering);

% Fløde for investerere
Cash_flow(i)=Vinst_etter_skatt(i)-Yearly_drift(i)-Avskrivning(i);     % Kassafløde før driftkostnader
SUM_Cash_flow(i)=Cash_flow(i)+Ammortering(i);
  end

IRR= irr([[-Eget_kap,SUM_Cash_flow]])
%Pris for kunde år 1
Pris=Leasing+EL_VP*elpris
Pris_kWh=Pris/Levert_Varmne
%Pris/ kWh






