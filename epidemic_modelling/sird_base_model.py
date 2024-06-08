# Beta = contact rate
# Gamma = recovery rate
# Delta = death rate
# Average mortality rate = Delta/Gamma
# R0 (contact number) = Beta/(Gamma + Delta)

# dS/dt = -Beta * S * I
# dI/dt = Beta * S * I - (Gamma * I) - (Delta * I)
# dR/dt = Gamma * I
# dD/dt = Delta * I
# S + I + R + D = N


# Infection over time
# I(t) is proprtional to exp(Beta * ((S - 1/R0)*I))

from scipy.integrate import solve_ivp
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

initial_conditions = {
    "population": 60000000,
    "cases": 3000,
    "deaths": 80,
    "recovered": 20,
}


class SIRD:
    def __init__(self, R0: float = None, M: float = None, P: float = None, beta: float = None, gamma: float = None, delta: float = None):
        if R0 is not None and M is not None and P is not None:
            # Model parameters given R0, M, P
            # R0: Basic Reproductive Rate [people]
            self.R0 = R0
            # M: mortality rate ratio
            self.M = M
            # P: Average infectious period [days]
            self.P = P # 5.1 days

            # Calculate beta, gamma, delta from R0, M, P
            self.beta = self.R0 / self.P
            self.gamma = (1 - self.M) / self.P
            self.delta = self.M / self.P
        elif beta is not None and gamma is not None and delta is not None:
            # Model parameters given beta, gamma, delta
            self.beta = beta
            self.gamma = gamma
            self.delta = delta

            # Calculate R0, M, P from beta, gamma, delta
            self.P = 1 / (self.gamma + self.delta)
            self.R0 = self.beta * self.P
            self.M = self.delta / (self.gamma + self.delta)
        else:
            raise ValueError("Either (R0, M, P) or (beta, gamma, delta) must be provided")

    def dSdt(self, S: int, I: int, beta: float):
        """
        Compute Susceptible parameter over time

        Parameters:
        ------------
        S: Susceptible population
        I: Infected population
        beta: Contact rate

        Returns:
        ------------
        dSdt: Susceptible population over time
        """
        return -beta * S * I

    def dIdt(self, S: int, I: int, beta: float, gamma: float, delta: float):
        """
        Compute Infected parameter over time

        Parameters:
        ------------

        S: Susceptible population
        I: Infected population
        beta: Contact rate
        gamma: Recovery rate
        delta: Death rate

        Returns:
        ------------
        dIdt: Infected population over time
        """
        return beta * S * I - gamma * I - delta * I

    def dRdt(self, I: int, gamma: float):
        """
        Compute Recovered parameter over time

        Parameters:
        ------------
        I: Infected population
        gamma: Recovery rate

        Returns:
        ------------
        dRdt: Recovered population over time
        """
        return gamma * I

    def dDdt(self, I: int, delta: float):
        """
        Compute Deaths parameter over time

        Parameters:
        ------------
        I: Infected population
        delta: Death rate

        Returns:
        ------------
        dDdt: Deaths population over time
        """

        return delta * I

    def eqns(self, t: int, y: tuple, beta: float, gamma: float, delta: float):
        S, I, R, D = y
        # print(beta, gamma, delta)
        return [
            self.dSdt(S, I, beta),
            self.dIdt(S, I, beta, gamma, delta),
            self.dRdt(I, gamma),
            self.dDdt(I, delta),
        ]

    def setup(self, population: int, cases: int, recovered: int, deaths: int):
        # Compute initial values
        self.population = population
        initial_S = (population - cases - recovered - deaths) / population
        initial_R = recovered / population
        initial_D = deaths / population
        initial_I = cases / population
        self.y0 = [initial_S, initial_I, initial_R, initial_D]

        # Coeffs are computed in the __init__ func

        # Compute coefficients
        # self.beta = 0.2
        # self.gamma = 0.7
        # self.delta = 0.1

        # self.beta = self.R0 / self.P
        # self.gamma = (1 - self.M) / self.P
        # self.delta = self.M / self.P

    def solve(self, initial_conditions: dict, time_frame: int = 300):
        """
        Solve the SIRD model

        Parameters:
        ------------
        initial_conditions: dict
            Dictionary containing initial conditions for the model
            keys: population, cases, recovered, deaths
        time_frame: int
            Number of days to run simulation for

        Returns:
        ------------
        self: SIRD
            Returns the instance of the class
        """

        self.setup(
            initial_conditions["population"],
            initial_conditions["cases"],
            initial_conditions["recovered"],
            initial_conditions["deaths"],
        )

        t_span = (
            0,
            time_frame,
        )  # tf is number of days to run simulation for, defaulting to 300

        self.soln = solve_ivp(
            self.eqns,
            t_span,
            self.y0,
            args=(self.beta, self.gamma, self.delta),
            t_eval=np.linspace(0, time_frame, time_frame * 2),
        )
        return self

    def get_params(self):
        """
        Return the model parameters after a simulation has been run

        Returns:
        ------------
        dict: dictionary containing model parameters
        """
        params = self.soln.y[:, -1]
        return {"S": params[0], "I": params[1], "R": params[2], "D": params[3], "Sum params:" : params.sum()}

    def plot(self, ax=None, susceptible=True):
        S, I, R, D = self.soln.y
        t = self.soln.t
        N = self.population

        print(f"For a population of {N} people, after {t[-1]:.0f} days there were:")
        print(f"{D[-1]*100:.1f}% total deaths, or {D[-1]*N:.0f} people.")
        print(f"{R[-1]*100:.1f}% total recovered, or {R[-1]*N:.0f} people.")
        print(
            f"At the virus' maximum {I.max()*100:.1f}% people were simultaneously infected, or {I.max()*N:.0f} people."
        )
        print(
            f"After {t[-1]:.0f} days the virus was present in less than {I[-1]*N:.0f} individuals."
        )

        if ax is None:
            fig, ax = plt.subplots()

        ax.set_title("Covid-19 spread")
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Number")
        if susceptible:
            ax.plot(t, S * N, label="Susceptible", linewidth=2, color="blue")
        ax.plot(t, I * N, label="Infected", linewidth=2, color="orange")
        ax.plot(t, R * N, label="Recovered", linewidth=2, color="green")
        ax.plot(t, D * N, label="Deceased", linewidth=2, color="black")
        ax.legend()

        return ax
