# -*- coding: utf-8 -*-
"""
Plotting functions for key nutrition model results.

@author: Kelsey Grantham <kelsey.grantham@burnet.edu.au>
"""

### Get distinct RGB colors for use in bar charts

def get_cmap(N):
    """
    Returns a function that maps each index in 0, 1, ..., N-1 to a distinct
    RGB color.
    """
    import matplotlib.cm as cmx
    import matplotlib.colors as colors
    color_norm = colors.Normalize(vmin=0, vmax=N-1)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv')
    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)
    return map_index_to_rgb_color


### Stacked bar charts for nutrition spending

def plotallocations(budgetDictBefore, budgetDictAfter):
    """
    Plot original and optimal program allocations as a stacked bar chart.
    
    Arguments:
        budgetDictBefore - a dictionary mapping program names to original
            program allocations
        budgetDictAfter - a dictionary mapping program names to optimized
            program allocations
    """
    import matplotlib.pyplot as plt    
    alloc = zip(budgetDictBefore.values(), budgetDictAfter.values())
    n_groups = 2
    fig, ax = plt.subplots()
    index = range(n_groups)
    bar_width = 0.4
    tick_pos = [i+(bar_width/2) for i in index]
    opacity = 0.5
    cmap = get_cmap(len(alloc)+1)
    alloc.insert(0, (0.0, 0.0))
    for p in xrange(len(alloc)-1):
        plt.bar(index, alloc[p+1], bar_width,
                alpha=opacity,
                color=cmap(p),
                bottom=(sum([pair[0] for pair in alloc[:p+1]]),
                        sum([pair[1] for pair in alloc[:p+1]])),
                label=budgetDictBefore.keys()[p])
    plt.ylabel('$')
    plt.title('Annual Nutrition Intervention Spending', fontsize=16)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
               ncol=2, fontsize=10, frameon=False)
    plt.xticks(tick_pos, ('Original', 'Optimized'), fontsize=14)
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    ax2 = ax.twinx()
    ax2.set_xlim(x1, x2)
    ax2.set_ylim(y1, y2)
    plt.xlim([min(tick_pos)-bar_width, max(tick_pos)+bar_width])
    plt.tight_layout()
    plt.show()


def plotalloccascade(budgetcascade):
    """
    Plot investment cascade, the optimized program allocations at several
    multiples of the original budget, as a stacked bar chart.

    Arguments:
        budgetcascade - a dictionary mapping multiples of the original budget
            to a dictionary mapping program names to optimized program
            allocations
    """
    import matplotlib.pyplot as plt
    cascade = zip(budgetcascade.keys(), budgetcascade.values())
    increments = [x for (x,y) in sorted(cascade)]
    allocdicts = [y for (x,y) in sorted(cascade)]
    vals = [allocdict.values() for allocdict in allocdicts]    
    alloc = zip(*vals)
    n_groups = len(budgetcascade)
    fig, ax = plt.subplots()
    index = range(n_groups)
    bar_width = 0.4
    tick_pos = [i+(bar_width/2) for i in index]
    opacity = 0.5
    cmap = get_cmap(len(alloc)+1)
    alloc.insert(0, (0.0,)*len(increments))
    for p in xrange(len(alloc)-1):
        bottom = [sum([prog[i] for prog in alloc[:p+1]]) for i in \
                    range(len(increments))]
        bottomvals = tuple(bottom)
        plt.bar(index, alloc[p+1], bar_width,
                alpha=opacity,
                color=cmap(p),
                bottom=bottomvals,
                label=allocdicts[0].keys()[p])
    plt.ylabel('$')
    plt.title('Nutrition Intervention Spending', fontsize=16)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
               ncol=2, fontsize=10, frameon=False)
    tick_labels = tuple([str(inc) for inc in increments])
    plt.xticks(tick_pos, tick_labels, fontsize=14)
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    ax2 = ax.twinx()
    ax2.set_xlim(x1, x2)
    ax2.set_ylim(y1, y2)
    plt.xlim([min(tick_pos)-bar_width, max(tick_pos)+bar_width])
    plt.tight_layout()
    plt.show()
    
    
### placeholder very simple unfancy function to plot time series.  Added by Ruth.
def plotTimeSeries(years, yBaseline, yOptimised, title):
    import matplotlib.pyplot as plt
    plt.plot(years, yBaseline, label = 'baseline')
    plt.plot(years, yOptimised, label = 'optimised')
    plt.ylabel('objective')
    plt.title(title)
    plt.legend()
    plt.show()    
    
def plotRegionalBOCs(regionalBOCs, regionList, optimise):
    import matplotlib.pyplot as plt
    for region in range(len(regionList)):
        regionName = regionList[region]
        x = regionalBOCs['spending'][region]
        y = regionalBOCs['outcome'][region]
        plt.plot(x, y, label = regionName)
    plt.title('BOCs')
    plt.ylabel(optimise)
    plt.xlabel('spending')
    plt.legend()
    plt.show()

def plotTradeOffCurves(tradeOffCurves, regionList, optimise):
    import matplotlib.pyplot as plt
    for region in range(len(regionList)):
        regionName = regionList[region]
        x = tradeOffCurves[regionName]['spending']
        y = tradeOffCurves[regionName]['outcome']
        plt.plot(x, y, label = regionName)
    plt.title('trade off curves')
    plt.ylabel(optimise+' cases averted')
    plt.xlabel('additional $')
    plt.legend()
    plt.show()




    
        
    
    