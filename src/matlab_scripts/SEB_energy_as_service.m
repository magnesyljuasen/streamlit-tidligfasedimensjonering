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
AsplanViak_varme=20;                  % 20% av entreprenaden til Asplan Viak
AsplanViak_sol=10;                    % 10% av entreprenaden til Asplan Viak
Enova=1600;                           % Støtte fra 1600 NOK / kW - installert varmeeffekt på varmepumpe
Avkastningskrav_bygg=4;               % Byggets avkastningskrav, brukes til å sett verdi på installsjonen.
%Investering

EffektVP=200;                         % Installert varmeeffekt (kW)
Levert_Varme=900000;                  % Levert varmebehov fra VP kWh
COP=3.5;
EL_VP=Levert_Varme/COP;
elpris=1;   % NOK / kWh  inkl alt uten mva

Boring=4.83*10^6;                     % Investering i brønnpark, komplett leveranse
VP=4*10^6;                            % Investering i varmepumpesentral, komplett leveranse
Reinvest_VP=2*700000;                 % Reinvestering i varmepumpe, ca. 20 % av investeringen i varmepumpesentral
Enova_bidrag=Enova*EffektVP;          % støtte fra Enova
Sol=0;


Arvode_AV_Varme=(Boring+VP-Enova_bidrag)*(AsplanViak_varme/100);
Arvode_AV_Sol=Sol*(AsplanViak_sol/100);

Investering=Boring+VP-Enova_bidrag+Arvode_AV_Varme+Sol+Arvode_AV_Sol    % Sum investering

Driftskostnad=50000;                                                    % Driftskostnad - årlig F-gass kontroll mm

Eget_kap=(1-Belaning)*Investering;

Lan=Investering-Eget_kap;
Resterende_Lan=Lan;

Leasing=450000;

Year=[0:15];
Reinvest_VP;
Reinvest_VP2=Reinvest_VP*(1+Inflasjon/100)^Ekonomisklevetid;

for i=1:Year(end)

%P&L

Yearly_fee(i)=Leasing*(1+Inflasjon/100).^Year(i);
Management(i)=-Investering*Managementfee/100;
Yearly_drift(i)=-Driftskostnad*(1+Inflasjon/100).^Year(i);
Reinvest(i)=-Reinvest_VP2/Ekonomisklevetid;
Avskrivning(i)=-Investering*0.025;
EBIT(i)=Yearly_fee(i)+Management(i)+Avskrivning(i)+Yearly_drift(i)+Reinvest(i);
Rentekostnad(i)=-Resterende_Lan*(Rentekost/100);
EBT(i)=EBIT(i)+Rentekostnad(i);
Yearly_Bolagsskatt(i)=min([0,-EBT(i)*Bolagsskatt/100]);
Vinst_etter_skatt(i)=EBT(i)+Yearly_Bolagsskatt(i);

 if i <= 100
  Ammortering(i)=-Lan/100;
  else
  Ammortering(i)=0
  end
  Resterende_Lan=Lan+sum(Ammortering);

% Fløde for investerere
Cash_flow(i)=Vinst_etter_skatt(i)-Yearly_drift(i)-Avskrivning(i);    % Kassafløde før driftkostnader
SUM_Cash_flow(i)=Cash_flow(i)+Ammortering(i);

end


% Beregner verdi av anlegget
Driftsnetto=(Levert_Varme-EL_VP)*elpris*(1+Inflasjon/100)^Year(end)+Yearly_drift(end)+Reinvest(end);
Verdi_anlegg=Driftsnetto/(Avkastningskrav_bygg/100);

% Avkastningskrav til fondet
IRR= irr([-Eget_kap,SUM_Cash_flow(1:end-1),(SUM_Cash_flow(end)+Verdi_anlegg-Resterende_Lan)])
%Pris for kunde år 1
Pris=Leasing+EL_VP*elpris
Pris_kWh=Pris/Levert_Varme
%Pris/ kWh
Arvode_AV_Varme
Arvode_AV_Sol








