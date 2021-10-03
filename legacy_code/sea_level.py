def eg_simplified(partition, election):
    seat_share = partition[election].wins("Rep") / len(partition)
    vote_share = partition[election].percent("Rep")
    return -((2 * vote_share) - seat_share - 0.5) # negative so that > 0 is advantage to Rep.

def get_seat_shares(partition, elections):
    return [partition[election].wins("Rep") / len(partition) for election in elections]

def get_vote_shares(partition, elections):
    return [partition[election].percent("Rep") for election in elections]

def ideal_simple_eg(vs):
    return [2*v - 0.5 for v in vs]

def get_simplified_egs(partition, elections):
    return [eg_simplified(partition, election) for election in elections]

def plot_many_seats(plans, elections, title):
    vote_shares = get_vote_shares(make_partition_from_districtr_csv("WI", graph, plans[0]), elections)
    ideal_egs = ideal_simple_eg(vote_shares)
    
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(vote_shares,
            marker='o',
            markersize=10,
            lw=5,
            label='Proportionality',
           )
#     ax.plot(ideal_egs,
#             marker='o',
#             markersize=10,
#             color='green',
#             lw=5,
#             label='Ideal Efficiency Gap',
#            )
    for plan in plans:
        partition = make_partition_from_districtr_csv("WI", graph, plan)
        seat_shares = get_seat_shares(partition, elections)
        P2_score = P2(partition, elections)
        if plan == "WI_enacted":
            plan = "Enacted"
        ax.plot(seat_shares,
                marker='o',
                linestyle='--',
                label=f'{plan}')
        
    ax.set_xticklabels([""] + elections)
    
    plt.ylim(0, 0.8)
    plt.axhline(0.5, color="black", alpha=0.8, label="50%")
    plt.legend()
    plt.xlabel("Election", fontsize=24)
    plt.ylabel("GOP Share", fontsize=24)
    plt.title(title, fontsize=24)
    
    plt.savefig(f"plots/{title.replace(' ','').replace(':','')}.png", dpi=300, bbox_inches='tight')
    plt.show()
    return
