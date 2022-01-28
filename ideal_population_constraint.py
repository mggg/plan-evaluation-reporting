from gerrychain import Partition 


class MyConstraints: 
  def __init__(self, func, bounds): 
     self.func = func
     self.bounds = bounds
  
  def __call__(self, *args, **kwargs): 
     lower, upper = self.bounds
     values = self.func(*args, **kwargs)
     return lower <=min(values) and max(values) <= upper
  
  @property
  def __name__(self):
        return "Bounds({},{})".format(self.func.__name__, str(self.bounds))

def ideal_population_constraint(partition, epsilon, ideal_pop):
   def population(partition): 
       return partition["population"].values()

   if ideal_pop is None:
     ideal_pop = sum(partition["population"].values())/len(partition["population"].keys())

   bounds = ((1-epsilon) * ideal_pop, (1+epsilon) * ideal_pop)

   return MyConstraints(population, bounds)
