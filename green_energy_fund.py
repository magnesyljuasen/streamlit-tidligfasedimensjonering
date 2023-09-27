import numpy_financial as npf

class GreenEnergyFund:
    def __init__(self):
        # Define economic parameters
        self.Rente = 3.75
        self.Inflasjon = 2
        self.Rente_Swapp_5 = 2.25
        self.Rentemarginal = 1.5
        self.Rentekost = 3.75
        self.Belaning = 0.30
        self.Ekonomisklevetid = 15
        self.Managementfee = 1
        self.Bolagsskatt = 22
        self.AsplanViak_varme = 20
        self.AsplanViak_sol = 10
        self.Enova = 1600
        self.Avkastningskrav_bygg = 4

        # Define investment parameters
        self.EffektVP = 200
        self.Levert_Varmne = 900000
        self.COP = 3.5
        self.EL_VP = self.Levert_Varmne / self.COP
        self.elpris = 1
        self.Boring = 4.83e6
        self.VP = 4e6
        self.Enova_bidrag = self.Enova * self.EffektVP
        self.Sol = 0

        self.Investering = (
            (self.Boring + self.VP - self.Enova_bidrag)
            * (1 + self.AsplanViak_varme / 100)
            + self.Sol * (1 + self.AsplanViak_sol / 100)
        )

        self.Driftskostnad = 50000

        self.Eget_kap = (1 - self.Belaning) * self.Investering

        self.Lan = self.Investering - self.Eget_kap
        self.Resterende_Lan = self.Lan

        self.Leasing = 0.102 * self.Investering

        self.Year = list(range(0, 16))

    def seb_15_year(self):
        # Initialize arrays to store results
        Yearly_fee = [0] * len(self.Year)
        Management = [0] * len(self.Year)
        Avskrivning = [0] * len(self.Year)
        Yearly_drift = [0] * len(self.Year)
        EBIT = [0] * len(self.Year)
        Rentekostnad = [0] * len(self.Year)
        EBT = [0] * len(self.Year)
        Yearly_Bolagsskatt = [0] * len(self.Year)
        Vinst_etter_skatt = [0] * len(self.Year)
        Ammortering = [0] * len(self.Year)
        Cash_flow = [0] * len(self.Year)
        SUM_Cash_flow = [0] * len(self.Year)

        # Calculate financial parameters
        for i in range(len(self.Year)):
            Yearly_fee[i] = self.Leasing * (1 + self.Inflasjon / 100) ** self.Year[i]
            Management[i] = -self.Investering * self.Managementfee / 100
            Avskrivning[i] = -self.Investering / self.Ekonomisklevetid
            Yearly_drift[i] = -self.Driftskostnad * (1 + self.Inflasjon / 100) ** self.Year[i]
            EBIT[i] = Yearly_fee[i] + Management[i] + Avskrivning[i] + Yearly_drift[i]
            Rentekostnad[i] = -self.Resterende_Lan * (self.Rentekost / 100)
            EBT[i] = EBIT[i] + Rentekostnad[i]
            Yearly_Bolagsskatt[i] = min([0, -EBT[i] * self.Bolagsskatt / 100])
            Vinst_etter_skatt[i] = EBT[i] + Yearly_Bolagsskatt[i]

            if i <= self.Ekonomisklevetid:
                Ammortering[i] = -self.Lan / self.Ekonomisklevetid
            else:
                Ammortering[i] = 0
            self.Resterende_Lan = self.Lan + sum(Ammortering)
            Cash_flow[i] = Vinst_etter_skatt[i] - Yearly_drift[i] - Avskrivning[i]
            SUM_Cash_flow[i] = Cash_flow[i] + Ammortering[i]

        IRR = npf.irr([-self.Eget_kap] + SUM_Cash_flow)

        # Calculate the price for the customer in year 1
        Pris = self.Leasing + self.EL_VP * self.elpris
        Pris_kWh = Pris / self.Levert_Varmne

        print("Investment:", self.Investering)
        print("Internal Rate of Return (IRR): {:.2%}".format(IRR))
        print("Price for the customer in year 1:", Pris)
        print("Price per kWh:", Pris_kWh)

    def seb_energy_as_a_service(self):
        # Define investment parameters for script2
        EffektVP = 200
        Levert_Varme = 900000
        COP = 3.5
        EL_VP = Levert_Varme / COP
        elpris = 1
        Boring = 4.83e6
        VP = 4e6
        Reinvest_VP = 2 * 7e5
        Enova_bidrag = self.Enova * EffektVP
        Sol = 0

        Arvode_AV_Varme = (Boring + VP - Enova_bidrag) * (self.AsplanViak_varme / 100)
        Arvode_AV_Sol = Sol * (self.AsplanViak_sol / 100)

        Investering = Boring + VP - Enova_bidrag + Arvode_AV_Varme + Sol + Arvode_AV_Sol

        Driftskostnad = 50000
        Eget_kap = (1 - self.Belaning) * Investering
        Lan = Investering - Eget_kap
        Resterende_Lan = Lan
        Leasing = 450000

        # Define the number of years
        Year = list(range(0, 16))
        Reinvest_VP
        Reinvest_VP2 = Reinvest_VP * (1 + self.Inflasjon / 100) ** self.Ekonomisklevetid

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

        # Calculate financial parameters for script2
        for i in range(len(Year)):
            Yearly_fee[i] = Leasing * (1 + self.Inflasjon / 100) ** Year[i]
            Management[i] = -Investering * self.Managementfee / 100
            Yearly_drift[i] = -Driftskostnad * (1 + self.Inflasjon / 100) ** Year[i]
            Reinvest[i] = -Reinvest_VP2 / self.Ekonomisklevetid
            Avskrivning[i] = -Investering * 0.025
            EBIT[i] = Yearly_fee[i] + Management[i] + Avskrivning[i] + Yearly_drift[i] + Reinvest[i]
            Rentekostnad[i] = -Resterende_Lan * (self.Rentekost / 100)
            EBT[i] = EBIT[i] + Rentekostnad[i]
            Yearly_Bolagsskatt[i] = min([0, -EBT[i] * self.Bolagsskatt / 100])
            Vinst_etter_skatt[i] = EBT[i] + Yearly_Bolagsskatt[i]

            if i <= 100:
                Ammortering[i] = -Lan / 100
            else:
                Ammortering[i] = 0
            Resterende_Lan = Lan + sum(Ammortering)
            Cash_flow[i] = Vinst_etter_skatt[i] - Yearly_drift[i] - Avskrivning[i]
            SUM_Cash_flow[i] = Cash_flow[i] + Ammortering[i]

        # Calculate the value of the facility
        Driftsnetto = (Levert_Varme - EL_VP) * elpris * (1 + self.Inflasjon / 100) ** Year[-1] + Yearly_drift[-1] + Reinvest[-1]
        Verdi_anlegg = Driftsnetto / (self.Avkastningskrav_bygg / 100)

        # Calculate the internal rate of return for script2
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

# Create an instance of the GreenEnergyFund class and calculate both scripts
green_energy = GreenEnergyFund()
print("15 år:")
green_energy.seb_15_year()
print("Energy as a service:")
green_energy.seb_energy_as_a_service()
