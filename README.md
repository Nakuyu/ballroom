# Ballroom

> *what if i just... let them talk to each other*

I built this out of pure curiosity. just because I wanted to see what happens when you give a bunch of opinionated(trying to opinionate them) agents a social network. 
This also is to increase my understanding of social networks and multi-agent environments which i find very interesting. 
polarization. echo chambers, these are basics but detailed observations have not yet been made. 

---

## what it does

Agents each with beliefs, goals, a personality they didn't choose wake up every tick, look at their feed, and decide what to do. Post something. Agree with someone. Quietly unfollow a person they used to like. The kind of stuff that happens in a social network, basically.


```bash
# install
pip install -e .

# copy env (you'll need an API key in there)
cp .env.example .env

# run it (real LLM calls)
ballroom

# run it without spending money (mock mode, deterministic)
ballroom --mock

# run longer
ballroom --mock --ticks 200
```

---

## v0.1 - what's the system right now

- **6 agents** split across 3 factions: Builders, Regulators, Researchers. They don't get along great.
- **Belief vectors** - not personality adjectives. Actual numerical positions on topics, with confidence levels and load-bearing flags (beliefs they'll defend i think).
- **5 actions per tick** - POST, COMMENT, LIKE, FOLLOW, UNFOLLOW, IGNORE. One per agent per tick. No monologuing.
- **Tick scheduler** - randomized order, probabilistic action. Keeps things from being too neat.
- **Event log** - everything written down.
- **Analytics** - polarization scores, influence rankings, echo chamber coefficient.
- **Mock mode** - for when you want to poke around without burning through tokens. (sort of trial rn not polished)

---

## how a tick actually works

For each agent (shuffled order, keeps it honest):

1. Build their context - who they are, what they believe, what's on their feed, who they trust, and what they remember (memory exists, but it fades)
2. Ask the LLM: *what do you do?* (JSON back, one action)
3. Parse it
4. Apply it to the feed
5. Agent remembers what happened, updates their interactions with people

The one-action-per-tick constraint is load-bearing. It forces bounded attention. Somewhat real(not yet) social dynamics, not infinite meta-discussion (no infinite monologue).


---

## where this is going

things i want to try, roughly in order of how much they're keeping me up at night:

- memory decay + summarization (do you remember everything? neither do they)
- recommendation algorithms -  what changes when the feed is engagement-ranked vs chronological?
- a news event injection - "the AI incident" - and watching how different factions react
- multi-model architecture: Planner / Writer / Critic
- graph visualization so you can *see* the echo chambers forming
- group formation
- reputation and trust dynamics
- belief update mechanisms - what actually changes someone's mind here 
- also all the factors will be mostly changed according to what i am trying out.

---

## decision track

problems we ran into, what we tried, what we're still figuring out.
 
## the sycophancy problem
 
agents agreed with everything. same argument, opposite argument too positive either way. useless for simulating a social network where people actually push back.
So each agent is given 2-3 load-bearing beliefs they defend (just argue lol) even when challenged, plus competing goals so they have real reasons to disagree. still not perfect but the arguments feel real now tho.
 
---
 
## the memory problem
 
agents forgot everything by many ticks and well kinda got memory loss. decay rate was 0.98 per tick memory half-life of ~34 ticks. changed it to 0.99, which doubles the half-life to ~69 ticks.
 
---
 
## the belief update problem
 
first version new_belief = old_belief × trust × learning_rate × evidence_weight, cranking up the learning rate just caused wild swings instead, 
direct deltas that is LLM explicitly proposes the amount of change works for now but downside being that it could shift alot,
so i m thinking of a hybrid approach here where i try to understand the proposed shift by the llm and calculate actual shift according to that 
so something like actual_delta = proposed_delta * trust_modifier * resistance_modifier , this way controlling the social dynamics sort of. still learning 
Also theres factions if you notices so the belief base is set by which faction youre i, which is like being born somewhere decides what youre initial beliefs
will be (How odd no?), but yeah since this is a simulation ill consider either keeping initial factions or somehow will think of a way that people with similar
belief can form a faction themselves.

---
 
## the topic problem
 
every agent talked about well very few topics, so everyone kept finding common ground. 
I m expanding the topics as much as i can myself and get some references on topics and make a huge topic list maybe.

---
 
## the echo chamber problem
 
added a global feed that surfaces posts from outside the follow field view but still needs to fixed, weighted by engagement the posts. still tuning the ratio.
 
---
 
## the engagement problem
 
84% of actions were comments,
follow rate is at 4% - up from zero, so thats good but this needs huge improvements here, i m reading up some established research and will tag it if i pick ideas from them.

---
 
## its all the same

this could happen that the network polarization  might flatten and well it ll be a boring network after a huge number of ticks but i dont want that so i m thinking 
of something like strong priors resist the change over time and exposure to some extreme position doenst shift the agent belief drastically. 
Gotta have some precautions
might need a character layer above the belief system that filters what updates are even allowed.
 
---

## a note

this is just me being curious about how social dynamics emerge from simple rules.
    just a little terrarium of opinions.
also Ill appreciate any advice given to me. Thanks for reading

---

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)