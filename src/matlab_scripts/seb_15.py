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

# Define investment parameters
EffektVP = 200
Levert_Varmne = 900000
COP = 3.5
EL_VP = Levert_Varmne / COP
elpris = 1
Boring = 4.83e6
VP = 4e6
Enova_bidrag = Enova * EffektVP
Sol = 0

Investering = (Boring + VP - Enova_bidrag) * (1 + AsplanViak_varme / 100) + Sol * (1 + AsplanViak_sol / 100)

Driftskostnad = 50000

Eget_kap = (1 - Belaning) * Investering

Lan = Investering - Eget_kap
Resterende_Lan = Lan

Leasing = 0.102 * Investering

Year = list(range(0, 16))

# Initialize arrays to store results
Yearly_fee = [0] * len(Year)
Management = [0] * len(Year)
Avskrivning = [0] * len(Year)
Yearly_drift = [0] * len(Year)
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
    Avskrivning[i] = -Investering / Ekonomisklevetid
    Yearly_drift[i] = -Driftskostnad * (1 + Inflasjon / 100) ** Year[i]
    EBIT[i] = Yearly_fee[i] + Management[i] + Avskrivning[i] + Yearly_drift[i]
    Rentekostnad[i] = -Resterende_Lan * (Rentekost / 100)
    EBT[i] = EBIT[i] + Rentekostnad[i]
    Yearly_Bolagsskatt[i] = min([0, -EBT[i] * Bolagsskatt / 100])
    Vinst_etter_skatt[i] = EBT[i] + Yearly_Bolagsskatt[i]
    
    if i <= Ekonomisklevetid:
        Ammortering[i] = -Lan / Ekonomisklevetid
    else:
        Ammortering[i] = 0
    Resterende_Lan = Lan + sum(Ammortering)
    Cash_flow[i] = Vinst_etter_skatt[i] - Yearly_drift[i] - Avskrivning[i]
    SUM_Cash_flow[i] = Cash_flow[i] + Ammortering[i]

IRR = npf.irr([-Eget_kap] + SUM_Cash_flow)

# Calculate the price for the customer in year 1
Pris = Leasing + EL_VP * elpris
Pris_kWh = Pris / Levert_Varmne

print("Investment:", Investering)
print("Internal Rate of Return (IRR): {:.2%}".format(IRR))
print("Price for the customer in year 1:", Pris)
print("Price per kWh:", Pris_kWh)
