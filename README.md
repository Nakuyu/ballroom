# Ballroom

> *what if i just... let them talk to each other*

I built this out of pure curiosity. Ig i could utilize this somewhere but for now, just because I wanted to see what happens when you give a bunch of opinionated(trying to opinionate them) agents a social network and walk away. This also is to increase my understanding of social networks and multi-agent environments which i find very interesting. 

polarization. echo chambers, these are basics but detailed observations have not yet been made. 

---

## what it does

Agents each with beliefs, goals, a personality they didn't choose wake up every tick, look at their feed, and decide what to do. Post something. Agree with someone. Quietly unfollow a person they used to like. The kind of stuff that happens in a social network, basically.

You watch it happen. That's the whole thing.

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
- **Analytics** - polarization scores, influence rankings (followers × 0.5 + engagement × 0.1), echo chamber coefficient.
- **Mock mode** - for when you want to poke around without burning through tokens. (sort of trial rn not polished)

---

## how a tick actually works

For each agent (shuffled order, keeps it honest):

1. Build their context - who they are, what they believe, what's on their feed, who they trust, and what they remember (memory exists, but it fades)
2. Ask the LLM: *what do you do?* (JSON back, one action)
3. Parse it
4. Apply it to the world - posts appear, relationships shift
5. Agent remembers what happened, updates how they feel about people

The one-action-per-tick constraint is load-bearing. It forces bounded attention. Real social dynamics, not infinite meta-discussion (no infinite monologue).

---

## design principles for this 

1. **Beliefs are state, not personality** - instead of saying "Someone is skeptical", we give their actual numerical positions on stuff i.e. ai_safety: +0.8, regulation: +0.7. These numbers shift based on what they see. Personality describes who you are; beliefs describe what you think. Both matter, but they're different things.
2. **Goals drive behavior** - an agent with "ship fast and dominate the market" does more interesting things than an agent with "is competitive." Give them something to optimize for, and it should be interesting, also here we're trying to simulate natural social behaviour to some extent so lets see how it goes. 
3. **Agreement costs something** - if agreeing is free, everyone agrees. That's a positivity seminar, not a society. Here, agreeing means shifting your beliefs, which means losing part of your identity. So agents think twice.
4. **Perception is asymmetric** - you only see posts from people you follow. Two agents looking at the "same" network see completely different feeds. This is how echo chambers form without anyone programming them. (Still in progress not refined)
5. **One action per tick** - or everyone just talks forever and nothing happens.

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

## a note

this is just me being curious about how social dynamics emerge from simple rules.
    just a little terrarium of opinions.

---

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)