from itertools import combinations
import numpy as np

def create_confidence_boxplot(axs, map, sensitive_events, custom_name = None):
    if type(sensitive_events) == str: sensitive_events = [sensitive_events]
    
    Kss = []
    Css = []

    # Get the Ks and Cs for different background sizes
    for i in range(1,5):
        Ks, Cs = map.distribution_LKC(i, sensitive_events)
        Kss.append(Ks)
        Css.append(Cs)
    
    # The odds at least one of the events happen
    prob_line = sum(sum(map.pr_e(list(comb)) for comb in combinations(sensitive_events, i+1))*(1 if i%2==0 else -1)
                      for i in range(len(sensitive_events)))
    
    # Create the plot
    axs.boxplot(Css)

    if custom_name != None:
        axs.set_title(f"Odds {custom_name}")
    else:
        axs.set_title(f"Odds" + "".join(f" '{sens}'," for sens in sensitive_events)[:-1])

    axs.axhline(y = prob_line, color = 'r', linestyle = '-', linewidth = 1.1) 
    axs.set_ylabel("Odds for Sensitive")
    axs.set_xlabel("Background Size")


def fix_stacking(log_results):
    # Random offsets to stop point staking
    np.random.seed = 103349     
    random_variations = np.random.normal(0, 0.08, size=len(log_results))
    log_results["M Confidence Privacy"] = log_results["Confidence Privacy"] * (1+random_variations) + 0.1*random_variations
    log_results.loc[log_results["M Confidence Privacy"] < 0, "M Confidence Privacy"] = 0

    random_variations = np.random.normal(0, 0.05, size=len(log_results))
    log_results["M Max C"] = log_results["Max C"] + random_variations
    log_results.loc[log_results["Max C"] == 1, "M Max C"] = 1
    log_results.loc[log_results["M Max C"] > 1, "M Max C"] = 1
    log_results.loc[log_results["M Max C"] < 0, "M Max C"] = 0

    return log_results