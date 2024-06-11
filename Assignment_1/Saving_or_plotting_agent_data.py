from vi import Agent, Simulation, Config
import polars as pl
import seaborn as sns

#class inheriting Agent behaviour
class Particle(Agent): 

#to make our own behaviour, make an update function
    def update(self):
        return super().update()




df = (
(

    Simulation(Config(duration = 5*60, fps_limit = 0,seed = 1))
    .batch_spawn_agents(100,Particle,images= ["Assignment_0/images/green.png"])
    .run()
    .snapshots            #to show the data of each Agent
    .group_by(["frame","image_index"])
    .agg(pl.count("id").alias("agents"))
    .sort(["frame", "image_index"])
)
)

print(df)

plot = sns.relplot(x=df["frame"], y=df["agents"], hue=df["image_index"])
plot.savefig("agents.png", dpi=300)

