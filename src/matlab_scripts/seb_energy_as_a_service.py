import numpy_financial as npf

# Define economic parameters
Rente = 3.75
Inflasjon = 2
Rente_Swapp_5 = 2.25
Rentemarginal = 1.5
Rentekost = 3.75
Belaning = 0.30
Ekonomisklevetid = 15
Managementfee = 1
Bolagsskatt = 22
AsplanViak_varme = 20
AsplanViak_sol = 10
Enova = 1600
Avkastningskrav_bygg = 4

# Define investment parameters
EffektVP = 200
Levert_Varme = 900000
COP = 3.5
EL_VP = Levert_Varme / COP
elpris = 1
Boring = 4.83e6
VP = 4e6
Reinvest_VP = 2 * 7e5
Enova_bidrag = Enova * EffektVP
Sol = 0

Arvode_AV_Varme = (Boring + VP - Enova_bidrag) * (AsplanViak_varme / 100)
Arvode_AV_Sol = Sol * (AsplanViak_sol / 100)

Investering = Boring + VP - Enova_bidrag + Arvode_AV_Varme + Sol + Arvode_AV_Sol

Driftskostnad = 50000
Eget_kap = (1 - Belaning) * Investering
Lan = Investering - Eget_kap
Resterende_Lan = Lan
Leasing = 450000

# Define the number of years
Year = list(range(0, 16))
Reinvest_VP
Reinvest_VP2 = Reinvest_VP * (1 + Inflasjon / 100) ** Ekonomisklevetid

# Initialize arrays to store results
Yearly_fee = [0] * len(Year)
Management = [0] * len(Year)
Yearly_drift = [0] * len(Year)
Reinvest = [0] * len(Year)
Avskrivning = [0] * len(Year)
EBIT = [0] * len(Year)
Rentekostnad = [0] * len(Year)
EBT = [0] * len(Year)
Yearly_Bolagsskatt = [0] * len(Year)
Vinst_etter_skatt = [0] * len(Year)
Ammortering = [0] * len(Year)
Cash_flow = [0] * len(Year)
SUM_Cash_flow = [0] * len(Year)

# Calculate financial parameters
for i in range(len(Year)):
    Yearly_fee[i] = Leasing * (1 + Inflasjon / 100) ** Year[i]
    Management[i] = -Investering * Managementfee / 100
    Yearly_drift[i] = -Driftskostnad * (1 + Inflasjon / 100) ** Year[i]
    Reinvest[i] = -Reinvest_VP2 / Ekonomisklevetid
    Avskrivning[i] = -Investering * 0.025
    EBIT[i] = Yearly_fee[i] + Management[i] + Avskrivning[i] + Yearly_drift[i] + Reinvest[i]
    Rentekostnad[i] = -Resterende_Lan * (Rentekost / 100)
    EBT[i] = EBIT[i] + Rentekostnad[i]
    Yearly_Bolagsskatt[i] = min([0, -EBT[i] * Bolagsskatt / 100])
    Vinst_etter_skatt[i] = EBT[i] + Yearly_Bolagsskatt[i]
    
    if i <= 100:
        Ammortering[i] = -Lan / 100
    else:
        Ammortering[i] = 0
    Resterende_Lan = Lan + sum(Ammortering)
    Cash_flow[i] = Vinst_etter_skatt[i] - Yearly_drift[i] - Avskrivning[i]
    SUM_Cash_flow[i] = Cash_flow[i] + Ammortering[i]

# Calculate the value of the facility
Driftsnetto = (Levert_Varme - EL_VP) * elpris * (1 + Inflasjon / 100) ** Year[-1] + Yearly_drift[-1] + Reinvest[-1]
Verdi_anlegg = Driftsnetto / (Avkastningskrav_bygg / 100)

# Calculate the internal rate of return
IRR = npf.irr([-Eget_kap] + SUM_Cash_flow[:-1] + [SUM_Cash_flow[-1] + Verdi_anlegg - Resterende_Lan])

# Calculate the price for the customer in year 1
Pris = Leasing + EL_VP * elpris
Pris_kWh = Pris / Levert_Varme
Arvode_AV_Varme
Arvode_AV_Sol

print("Investment:", Investering)
print("Internal Rate of Return (IRR): {:.2%}".format(IRR))
print("Price for the customer in year 1:", Pris)
print("Price per kWh:", Pris_kWh)
print("Arvode_AV_Varme:", Arvode_AV_Varme)
print("Arvode_AV_Sol:", Arvode_AV_Sol)
