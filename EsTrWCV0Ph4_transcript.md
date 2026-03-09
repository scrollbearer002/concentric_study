# YouTube Video Transcript

**Source:** [YouTube](https://www.youtube.com/watch?v=EsTrWCV0Ph4)

---

Hey, this is the definitive course on AI agents. I currently teach over 2,000 people how to use AI agents in both their personal and business lives and run a business that does over $4 million a year using AI agents. So, you don't

need any programming or pre-existing computer experience in order to make this course work for you. I myself don't have a formal computer science degree.

I've learned everything that I know watching free resources like you're doing now. This is also a general AI agents course, so you don't need to know any specific platform. This isn't just on codecs or claw code or anti-gravity,

but rather on all of them. So, wherever you guys are starting, you'll end up at the same place. No fluff. Here's what you're going to learn in this course.

First, I'll show you guys a demo where I'm controlling five AI agents, each with their own Chrome browsers as they interact with the web and perform economically valuable activities for me.

I wanted to frontload this course with a demo so you guys could see what we're working up to. And just a few months ago, what I'm doing here would have been considered absurd. Then, I'm going to cover the core AI agent workflow loop,

which works independent of which platform you're using. After that, I'm actually going to talk about and then sign up to the three major AI agent platforms right now. So, I'll sign up to codeex to anti-gravity and then cloud

code. And then after I'll cover what each platform is at the moment the best or the worst at. Then we're going to dive into foundational AI agent prompting techniques. So, selfmodifying agent instructions where the agent will

rewrite its own rules to minimize the number of errors made. Multi-agent MCP orchestration which is where we'll register codecs, Gemini, and Claude as MCP servers so you can manage multiple agents within a single conversation

thread. video to action pipelines where we'll teach agents to learn from YouTube videos instead of plain text alone.

Stochastic multi- aent consensus where we'll spawn multiple agents with the same prompt and then use their statistical spread in order to ideulate and improve things better. Agent chat rooms where you'll build centralized

places for agents to debate ideas, pushing them to much higher quality answers than before. Subagent verification loops where your agents will actually review each other's work in real time to catch things that one of

them might have missed. We'll talk prompt contracts. I'll show you guys reverse prompting and a bunch of other techniques as well. And finally, we'll chat about context management and improving the agent output quality

before closing out by discussing how to optimize um AI agent and then token pricing. So far, I haven't seen anybody on YouTube discuss most of what I cover in this course. So, for all intents and purposes, you guys consider this the

sauce. Please bookmark this video, subscribe to the channel, and let's get into it. First, I want to show you how powerful these agents can be when you learn how to distribute work across multiple Chrome instances and give each

sub agent their own workspace. What I have here is a simple list of leads from, let's just say, a conference. Now, we have fields like their websites, their LinkedIn description, their first name, their last name, but one thing is

missing, their email address. Now, just a year ago or so, that would have invalidated my ability to reach out to these leads. But now, because I possess their websites, I can actually spawn a bunch of Cloud Code agents, have them go

to the websites, and then have them interactively and dynamically fill out their contact forms. So, what just happened as I was talking was Claude went ahead and then opened up a bunch of different Chrome browsers for me. I'm

going to rearrange these to make it really easy to see. And so, this might be a little bit tough to see, but what these agents are all doing is they're independently navigating over to the contact fields of each of these

websites. They're then dynamically filling out fields like the first name, the last name, the email address, and so on and so forth. And then they're putting in a little bit of outreach that's templated, but then changes

depending on who they're reaching out to. These agents, through a combination of both research and then communication between each other in a shared chat room, are capable of doing things that any one agent might have taken many,

many hours to do before. This is what I'm going to work up to with you guys over the course of the rest of the next couple of hours. The main strength of AI agents is really their ability to parallelize, which is to run multiple

instances of each of them simultaneously while they accomplish a task. Now, right now, I would say most AI agents aren't as intelligent or as capable as a human being for any given need. But what they are much better at us then is being

fast. And so despite the fact that their accuracy might be a little bit lower than a human, their ability to oneshot stuff is worse than ours at the moment, they can run multiple instances of themselves simultaneously and try

multiple approaches over and over and over and over again in order to ultimately achieve much better results than we can. The key is you need to know a little bit about how they work under the hood. Then you need to be able to

combine them using elaborate prompt architecture like I'm going to show you in this course. So, why don't we start with one of the simplest, most foundational concepts before I actually guide you guys through signing up and

setting up these different agents. And I call this the core agent loop. To make a long story short, I think most of you probably have intuition about how agents do things. But really, what they're doing at the end of the day is they're

going through a loop over and over and over again. And this loop is composed of three major functions. The first is the observation step. And so here the agent is basically reading through all of its context. We're going to chat a little

bit more about how to optimize and manage that later. That includes things like its files, its previous tool calls.

It includes all of the system prompts, the clawed Gemini, and agents.mmds that you provide. If it does research in a previous step, it'll include the research from the internet. uh if you're feeding in multimodal data like vision

data, camera data, uh you know, audio files and so on and so forth, it'll include all of that. And so this agent, okay, is just in an environment and it's just always observing what's going around it at least to start in the

observation step. From there, it'll reason. And so this is the think step here. It'll consider based off of all of this context and based off of, you know, the user's highle goal, what do I do next? How should I plan my approach? And

nowadays, most agent coding platforms make use of like a dedicated reasoning step that you can actually click into and see, which I'll show you guys a little bit more of. And this provides a tremendous amount of interpretability,

accountability, and then steerability, which is really important that I think most people sleep on. After it's thought about things and basically wrote its own mini plan, it's time to actually act, right? And so, here's where it'll call

tools. It'll edit the files that it decided to uh do so earlier in the plan.

or maybe it'll run a command using command line interfaces, CLIs. After the action step is done, what it does is it gets the result of the tool call and then it feeds all of that stuff back into the observe step. So now we're

basically running through that loop again, just with a little bit more context. And so what occurs essentially is we just tend to grow bigger and bigger and bigger and bigger. If our initial context was a certain size, our

you know second loop it's a little bit bigger, our third loop it's a little bit bigger and fourth loop and so on and so forth. And what this is doing is this is basically stacking more and more tokens into the context that the model can then

use to plan its next step. What occurs after you go through this loop you know usually three or four times is eventually the model reaches a point called the definition of done.

And what the definition of done is, which I think a lot of people leave out of their agent prompts, which is probably why they're always underwhelmed by what happens, is it's the series of constraints and technical specifications

required for the model to conclude that it no longer needs to do this loop. Once it reaches this definition of done, okay, over and over and over and over again, it notices and then it changes routes. So, now it goes to the task

complete route where it generates a quick little final response for the user. Usually involves a nicely formatted answer, as I'm sure you guys know. Hey, Nick just finished your new thumbnail app build. And before

outputting it in a window either in anti-gravity or codeex or maybe cloud code in a packaged way that you guys are familiar with. And so obviously if you have any intuition about how AI works at this point, if you've ever communicated

with chat GPT or you know Claude or some other sort of desktop AI that's nestled into another application that you guys use, you'll probably know some of this stuff um just as like the foundation.

But I wanted to make it really explicit at the beginning of this course because we're going to return to each of these steps over and over and over again. And it turns out that you can heavily optimize all three of these. You can

optimize the hell out of the observe step. You can optimize the hell out of the think step. And understandably, you can optimize the hell out of the act step as well. That's what we're going to learn. Another point I'm going to make

in this course is that AI agents aren't just the large language models themselves. You know, I think neural networks and transformers are obviously super inherently interesting because they're these massive statistical things

and these beings that can that can do things. They can reason. They're very far removed from traditional computer programs. just 5 or 10 years ago. So, a lot of interest goes to the LLM, but I want you guys to know that the LLM

really is just a very small part of what most people consider AI agents these days. The LLM is of course your reasoning engine, right? Of course, it understands language and of course it makes decisions, but it's kind of like a

human being from like 20,000 years ago with like a spear in its hand, right?

without all of the infrastructure around human beings, without like your your house and your fireplace and your hearth and a place to sleep at the end of the night and a a society where people farm and produce resources and you have cars

that you can get and you traverse a lot of distance without all the tools and the architecture around the intelligence. The intelligence is actually quite limited in what it can do and that's where the rest of these

sections come into play. So tools much like human beings have the ability to read files, run code, search the web, call APIs and edit files. Okay, so too does this AI agent. Much like human beings have the ability to set a highle

goal and keep going until that task or goal is reached, you know, so too can agents. And much like human beings have some sort of persistent memory where we can keep track of things that we've done and then realize that some of those

things didn't work. So we got to take a slightly different tack the next time.

So too, agents have things like agents.mmd, claw.md, gemini.mmd, access to their conversation history, access to automemory files and skills. And so it's not actually just the LLM, for instance, that makes an agent work. It's really

all of these things multiplied by the fact that, you know, the LLM provides us like the ability to be a little bit flexible. And that's a really big different from just, you know, a chatbot and then an AI agent. A chatbot might

just be the LLM, okay? But an agent takes that that LLM and then it adds on tools, a reasoning loop, memory, and so on and so on and so forth. So, as a brief example, I'll use an agentic coding platform called Codeex. And down

here, I have a simple prompt where basically I just want this to do a bunch of research for me on creatine supplementation in men. And what I'm doing is I'm giving it a brief definition of done where I'm saying once

you've compiled 10 plus empirical sources, return a structured report. And I'm doing this because I want to demonstrate this loop to you. And so there are a bunch of other things that are popping up here. We have the actual

chat window up at the top and we have its response. But you'll notice that in between we have this sort of like grayed out section here. Okay. And this grayed out section is the thinking that the model is doing before it gets back to

us. And so basically, you know, if this was chatpt back from 2022 or so, all we would have gotten is this. But because I'm telling it to take actions in the real world, it's capable of one, observing, and so it observes all of

this text and all of its reply as context. Two, thinking. So it's capable of doing a bunch of thinking on what to do next. And then three, acting. And so then it's capable of saying, hm, the user probably wants me to do some

research. I have access to a few tools available. One of the tools lets me search the web. Let me pump in a search term. It then compiled all of this information and then it just repeated the same thing. It then with all this

context said, "Okay, I'm observing. Not only do I have these messages, but I also now have a bunch of research. Let me think about what to do next. Have I achieved the goal of the user compiling 10 plus empirical sources?" And you

know, after it's made its sort of observation and thought and reasoned about it, then it's deciding to act. And what it's ended up doing after 58 seconds is giving me this structured evidence report. So, this is an example

of something that might have looped two times, three times, but the more intelligent and capable these models are getting um the longer that they're running autonomously without us.

Hopefully, this isn't rocket science to anybody here, but in a nutshell, this is more or less what's always occurring non-stop every time you talk to a model.

With all that being said, let's really quickly cover how to set these different models up. I'm going to be using Codeex, Claude Code, and Anti-gravity. You don't need to know anything about any of these platforms in order to run these

examples. And if you're already very familiar with, let's say, I don't know, Claude Code and you've chosen to use that as your main agentic coding platform moving forward, you can skip over to the next section of the video.

But I want to make sure that we all have an equal playing ground here. We all understand how each of these platforms work under the hood. So there are three major platforms. The first is Codeex, which is owned, managed, and run by

OpenAI. The second is Claude Code, which is owned, managed, and run by Anthropic.

And the third is Google's anti-gravity, which as I'm sure you can imagine is owned, managed, and run by Google. In order to start with Codex, what you first have to do is sign up to an OpenAI account. The way you do so is just look

up OpenAI on Google, get to a page that looks anything like this, and then just go to the top right hand corner where it says try chat GPT. After that, you'll be taken to a page that looks something like this. You can continue with Google,

your phone, or whatever you want. And if you choose to chat with the model and then come back at any point in time, just head to the top right hand corner for that modal again. So I'm going to pretend that I haven't made an account

before and I'll continue with Google.

After some brief onboarding instructions, you'll have access to a page like this. But this is just chat GPT, which is more akin to a chatbot than anything else. We want to take this to the AI agent world. And so in order

to do that, we need to use their dedicated AI agentic coding platform, Codeex. So googling OpenAI's codeex or something like that will take you to a page that looks like this. And then you can just click download for Mac OS. By

the way, I'm on a Mac, so that button is automatically going to pop up for me.

But the Codeex app is now also available on Windows starting March 2024 and beyond. The way you install things on a Mac is you just take this window, drag Codex over to applications, and then you're done. Once you're inside, if you

wanted to build a website or something, just head over to this middle, create a new folder, call it whatever you want.

So I'll just go to downloads and then go new folder example.

Open it within it. And now you're inside of this folder here. You can ask the model to do whatever you want. And so what I'm going to say is make a brief portfolio site about Nick Sariah. Keep it super simple and minimal. It'll now

do some thinking. In our case, I actually have a design taste front-end skill which improves its ability to create like sleek, highquality looking designs. And now it's looking through my own workspace to put together this cool,

sexy site for me. I'm also going to ask it to open it. Uh, and the way that all AI agent platforms work now is you have the ability to put a cued message in, which you can also choose to send immediately via steer. In my case, I'll

just wait until it's done. It'll consume this open it message and then it'll just open it for me in a new tab. Once it's done, the open it message will be fed in and it's just going to open this for me in a new tab. Now, I'm kind of zoomed in

here. So, if I zoom in a little bit more, you'll see that this is just a a simple one-page site that says Nyx Drive builds clear modern digital work. Here's some information about me. And here's a contact page. Not rocket science, but

this is how easy it is to like build web stuff. Claude is pretty similar. Just Google Claude signup or something like that. And you'll be taken to a page that looks like this. Here you just enter your email address or in my case,

continue with Google. In Claude's case, in order to use Claude code, you do have to pay for it. And so there's a pro plan here that's $17 per month with an annual subscription or 20 bucks if build monthly. I'm not working for Claude or

anything like that. I don't have any sort of affiliation with Anthropic in that way. But I will say that I receive probably a 100 to 200x return on my investment with an Aentic coding platform, whether it's Claw or whether

it's Gemini or whether it's Codeex. So, my recommendation for you, if this seems a little bit steep, is bite the bullet, pay it, and learn whatever you can to make a return on investment with that money in the first month because this

stuff is really quite powerful. Assuming you're done, just type cloud code desktop download or something like that.

And you'll be taken to a page that looks like this, which allow you to download it for Mac OS, Windows, or even Windows ARM 64. So, I'm going to give my Mac OS thing a quick click. Then, I'll go to the top right hand corner. I'll just

open Cloud up just like I did with Codeex. That'll take me to a page like this. And then I just drag this over to the right. And then once you're done, you'll be taken to a chat page that looks something like this. What we

really want is we want this code button.

So I'm going to give that a click. Then here, all we need to do is just choose a folder to work in. And then we can put in a quick request. So I'm just going to choose a general folder next. Then I'm going to say bypass permissions, which

might seem a little bit scary to you, but it just makes the model act independently. Then finally, I'm going to say, hey, make a brief portfolio site about Nyx Drive. super simple and minimal. And so, just like Codeex

designed it a moment ago with its various UX uh features, we have the same thing here with Claude Code. It's going to ask to access some files in my folder. And in addition to having the message box, we also have this sort of

grayed out shining decal here, which is sort of its like thinking if you think about it, as well as its tool calls. And what it's going to do now is actually build me a brief little site. And then, just like I did before, I'll just say

open it.

That's going to ceue it and now I can have a conversation with Claude and now we have the actual portfolio which as you guys could see here is done in significantly more minimal fashion.

Okay, so this is Nick builder automation expert software engineer. Now unlike with chat GPT and then claude for anti-gravity odds are you probably already have like a Google or a Gmail account set up. So all you have to do is

just look up Google anti-gravity download then click download for Mac OS.

In my case I have Apple Silicon on Mac.

If you guys don't know what you have, just type about this Mac and then if it says Intel up here in chip, you're in Intel. If it's a M something, then you're Apple Silicon. And you can do something similar for Windows and Linux

as well. And once I give that a click, we'll be taken to a very similar looking page here. And then I can just drag anti-gravity over to applications. The very first time you open up anti-gravity, it'll look something like

this. In your case, maybe it'll be dark mode or maybe it'll be entirely light. I just have some styling settings, which is why mine might look a little different from yours. You may also have to log in unless Google logged you in

automatically. In my case, it logged me in automatically because I've used it before. Assuming that you've done that though, on the right hand side, you'll see an agent modal. And this agent modal is very similar to what we saw with

codeex and then claude code. All we have to do is just ask it to make a brief portfolio site about Nixive. And you'll see here that the UX is just a little bit different, right? We have a little generating tab down here. Obviously, we

have uh multiple settings with fast and Gemini 3.1 Pro. We have this little thinking tab. Uh, it tells you how long it's been doing it. If it has to do any web searches, it does so over here.

Hopefully, you guys are seeing these are all just flavors that are slightly different, but ultimately are the same thing. I'm just going to write open it.

That'll be added as a pending message, and then it'll open this up in a browser tab. As you see here, Gemini produced what I would probably consider to be the sexiest of all websites, which makes sense. Uh, one thing I'll talk about in

a moment is how much better it is at front-end design and so on and so forth.

And yeah, we have a very simple and and straightforward site here. So, um, this links to all of my resources, leftclick, YouTube, and so on and so forth. I probably like this one the best. From here on out, most of the conversations

and the user experiences are going to be really similar between Aenta coding platforms. So, while I am going to use multiple just to show you guys how some of their quirks interact, uh, for the most part, I want you guys to know that

the UX's are very very similar these days. Like the thinking tabs are going to be the same. Some people will probably say that there are slight differences between them and so on and so forth. For instance, I'm a big fan of

the little Space Invader icon that Cloud Code has. But for all intents and purposes, I'm just going to assume that you're picking up the UX here as you use these models and focus less on like the tiny little stuff and more on how to

orchestrate and then prompt these for higher quality responses. If you guys want to see like step-by-step walkthroughs of these platforms, I'm going to put some little links up above my left shoulder here, and you can click

on them anytime to go learn that sort of stuff. Next up, I want to talk about what makes these AI coding platforms different from one another. Not on a user experience um angle, but from an intelligence angle, from a what they

could do angle as well. So, as you saw there, there were three different models. There was Claude, which was wrapped around Claude code, Gemini, which was wrapped around anti-gravity, and then GPT, in my case, 5.4, which is

wrapped around codeex. And I think that each of these models are really similar at this point in intelligence- wise, but there are some pros and cons to each.

They basically like improve how they perform by a few percentage points. So Claude might be, you know, 2% better at these. You know, Gemini might be 5% better at these. GPT might be 1% better than these. I'm just pulling on numbers

out of my butt, but I'm making them really small because I do want to really drive home the point that these models are so gosh darn intelligent these days that these minor differences only make sense at the bleeding edge and at the

frontier. For most purposes, either of these are going to be sufficient. So, Claude has the most interpretable reasoning. You remember how I could click open that little reasoning tab a moment ago? Well, at least as of the

time of this recording, Claude is incredible at making that reasoning tab really, really interpretable. you know exactly what cloud is doing at basically every step of the process when you um use cloud code to visualize that

reasoning and that makes it really good for orchestration and then agentic workflows because you can see the decisions that the model is making in real time and in doing so you can also steer the model stop the model pause it

or give it new resources halfway through I can't say the same about both Gemini and GPT I think they're a lot less interpretable and it's a lot less accountable you know Claude is sort of a partner that you build things with along

the Whereas Gemini and GBT are almost just like I don't know, they're missiles. You set your target, you click the button, and then they go. Now, there are some cons. Claude is a little bit slower unless you use fast mode, which

is what I tend to use, although keep in mind that'll burn a ton of credits. And then I find that it's weaker at frontend or design than a model like Gemini.

Gemini is really good at design and frontends. As you guys just saw a moment ago, Claude picked a really minimalistic, sleek theme. Gemini did some upscale stuff that still looked sleek, clean, but had like that

isomorphic glass. And then GBT, maybe because of my design taste scale or something else, was kind of like more complex and had uh a little bit clunkier of a design. Well, in general, I find that this pattern remains the same.

Anytime I want to design a really clean front end, I'm going to use Gemini for that. It's also got superior multimodal abilities. That just means there's actual like endpoints using the Gemini API um where it can understand video.

Right now, Claude and GPT both really struggle with this. Although you can build custom pipelines to do that, which I'll show you guys about. It also has the ability to use a fast output, which means it writes really, really quickly

if need be. Um, but they don't have access to a dedicated fast mode where you could pay more money to use them really quick. I think it's the least interpretable of the models. And personally, I find the quality is quite

inconsistent. There's some days when I'll prompt it and it'll do quite incredible, then other days where I will prompt it and it will just absolutely crap the bed. you know, at least Claude's quite consistent in that way,

despite the fact that maybe it's a little bit worse at a few things.

Finally, there's GPT. There's the codec series of models, the 5.4 series of models. Now, these are the best at back-end programming. I think they're also the best at like um absolute mathematics, which probably feeds into

that. They're really great at test-driven development. And you know how I mentioned earlier Gemini and GBT are more like rockets that you point at a at a at a place and then they go. Um well these testdriven development

approaches essentially mean you just outline that definition of done and then it fires and just goes autonomously until it reaches that. There's also quite a big ecosystem of different apps and you know there's a lot of um

documentation online about how to use various GPT workflows and stuff like that because this was the first major player to the AI agent market. I'd give it sort of like a uh you know two out of three on the rest of these. I think

Claude is much better at its interpretability. It's much better at orchestration and stuff like that, but GPT being a model that just came out quite recently, a 5.4 anyway, is obviously sort of like topping the

charts right now on a lot of stuff. Just some caveats there. A lot of people treat this as like anathema for you to claim that, you know, Claude is better than GPT at this thing and Gemini is better than than Claude at that thing.

The reality is, as I mentioned and alluded to at the beginning, there are very minor differences between these models at this point. All of them are basically trained on the entirety of the internet as is. And so because of this,

um, the slight differences in capabilities in the model tend to have more to do with like when they were trained and how recent it is versus, you know, some inherent like cool new design technique. Really, they're just training

these galaxys sized brains on the entire internet at this point. So because we're talking about the LLM intelligences, you know, if like GPT was trained after Claude, GPT is probably going to be a little bit better in certain

circumstances. If Gemini is trained after GPT, it'll be better. But all that stuff resets with the next generation.

So though I am going to be showing you guys some cool multimmcp orchestration uh techniques later on, I want you to know that you don't have to treat all this super seriously. You can also just pick one model and then use that. Okay,

next up I want to chat agents.mmd and then how to build a selfmodifying and self-correcting system prompt that significantly minimizes the number of errors that you get as you build things with these AI agents. So for the

purposes of this demonstration, I'm going to be using anti-gravity and through it the Gemini series of models.

When you open up anti-gravity, you have a little window that looks like this.

Generally, I divide this into three panes. You have your explorer on the lefth hand side, your file editor in the middle, and then you have your agent on the right. And what I'm going to do for the purpose of this demo is I'll just

click open folder. And then I'm going to go to anti-gravity example and just open this up. Okay. And what I want to do here is I just want to show you how all of this stuff works to start. As you guys can see on the lefth hand side, we

have a file called gemini.md. Now, what occurs is when you talk to this model over here. Hey, what's up? Basically, what's occurring is this file is being prepended to the very top of a conversation chain. And so, if I open up

this file right now, you see how it's empty. There's nothing in it. Well, when I started this conversation and said, "Hey, what's up?" Okay, it knows that my name is Nick, but it does it knows this because of uh the fact that I'm signed

in as Nick. Now, I want you to see what happens if I paste in my name is Antonio Banderas. Refer to me as such. always always also always sign off super kawaii desu. So I'm going to go here to the top right hand corner and I'll say hey

what's up and after initializing a new model notice how it's now going to return something quite different to what we had a moment ago. The reason why is of course this gemini.md is just a

templated structured prompt that is basically always inserted into the beginning. Okay, the same thing applies with codecs. The same thing applies with claw code, but the names of the files are a little bit different. So if I was

in, let's say, codeex for instance, I wouldn't call this a gemini.md. I'd call this an agents.mmd. If I was in claude code, I wouldn't call this an agents.mmd. I'd call this a claude.mmd.

Whatever file you use here doesn't really change the idea. The idea is that at the very top of any prompt, you just have this file prepended to it. The reason why this is so powerful is because you now have the ability to

statically template out the same prompt over and over and over again on every independent session. This may seem like, well, why don't you just copy and paste the same thing in instead of having to use this elaborate file system

structure. And the reason why is because what you can do is at the very beginning of this file, you can actually contain within it like a list of lessons or learnings from previous instances. Then you can build in like a meta prompt

structure where before a model signs off, before it finishes whatever it's doing, it always updates that file with more and more and more knowledge. In that way, okay, you can build a highquality list of like memories,

preferences, and rules, not to mention things to avoid that significantly improves your agent's ability to operate over a long time scale. And just to show you guys what I mean, let me show you a diagram. In this hypothetical instance,

we're going to be using Gemini.m MD. And basically what'll occur every time is a new session is going to start over here.

The agent will first read gemini.md.

You'll then give it a task like hey build me a website that does whatever.

Now it'll return the website for me and then I'll say I don't like this no dark mode. After I give it its feedback of no dark mode rather than just correcting the build, it'll actually write that to my Gemini.m MD for next time, which

allow the agent to continue working with the rule applied. When the session ends and a new session starts, now the agent will read the Gemini MD, but the gemini.md will have an additional rule placed. Okay, if this is my file over

here, it'll say no dark mode. And that means the next time I ask it to build me a website or any sort of web property, it'll see no dark mode and then it won't make that mistake again. This lets your knowledge accumulate over sessions. The

first time that you use, you know, Gemini or Claude Code or or Codeex or whatever, you know, you're only going to have, let's say, one rule or one preference stored. And so the number of errors that the model makes, errors

relative to like your preferences will be pretty high. The second time that you use it, though, the number of errors or issues that it makes that don't line up with your preferences will go down. The third time, they'll go down further. The

fourth time, it'll go down further. Then the fifth time it'll go really really low to the point where maybe it makes zero errors at all. You can see that um sort of diagrammatically over here with when you start your thing has zero

rules. Okay. As it grows longer and longer and longer, you're writing more and more and more and more rules. Um the agents get better and better and better at uh understanding and then um anticipating as well your preferences.

So what does this actually look like in practice? Well, it's not all that difficult and you can just append or prepen this to any Gemini Claude or agents MD however you like. It also doesn't need to be this long. Although I

did want to go into a fair amount of detail here with you. So you can absolutely just turn this into like a I don't know a three or fourline snippet.

Essentially before we start any task read this entire file. This file contains a growing rule set that improves over time. At session start I want you to read the entire learned rule section before doing anything. How it

works. When the user corrects you or you make a mistake, immediately append a new rule to the learned rules section at the bottom of this file. Rules are numbered sequentially and written as clear imperative instructions. The format is

category never or always do X because Y.

And then here's some more formatting instructions. When do you add a rule?

Add a rule when the user explicitly corrects your output. When the user rejects a file approach or pattern, when you hit a bug caused by wrong assumption, or when the user states a preference. Okay? Okay. And then it'll

give some examples here of different rules in code. Then we have the learned rules down here. So what I'll do just to show you guys what this looks like is I'll say build me a simple portfolio site for Nick Sarif. And I'm going to

have it go accomplish a task for me. And then I'm inherently and intentionally going to give it some instructions. You see the very first thing it did was analyze the gemini.md. And so now it actually has this entire file as context

inside of its thread. You can't see that context here because obviously they don't want to just muck up your your conversation thread, but it is literally like if you just pasted this entire thing directly in. Okay, so it's going

to be reading that constantly as it's building out the rest of our website.

And you can see that it's like it's built some cool terminal display here.

It's using a library called Vit, which is probably like the best front-end library. Let's see what it does. Okay, this website is looking really really sexy, super clean, and it clearly went above and beyond uh with my spec.

However, I don't like how it's dark mode. So, what I'm going to do is go back here and then give it some instructions. Quit doing things in dark mode. And the idea here is when I give it an instruction like quit doing things

in dark mode, what it's going to do is it's going to take my message and then say, hey, let's update our gemini.md to never create applications in dark mode.

It's a user preference. If I scroll down here now, you can actually see that this style has been added. And so if the next time I run a model and instantiate anti-gravity, I say, "Hey, I'd like you to build me a website," it'll actually

have this up at the very very top of its prompt, meaning that I'm never ever going to have a dark mode website again.

In this way, this will continuously get closer and closer to my preferences until the number of rules become so exhaustive that, you know, it actually bes counterproductive. In practice, I haven't actually hit this limit yet. I

think this just gets better and better and better over time. But I could hypothetically see if you were to get to a point where there's a thousand independent rules, some of them would probably start stepping on its its toes.

Um, this sort of self-modifying claude agents or Gemini.mmd is a very very high ROI design pattern. So whatever you're building with an AI agent, whether you're using them for business, personal or programming tasks, I would always

recommend to have something like this in your directory. And as you can see, it's now modified the site. We don't actually have that anymore. A lot cleaner. And it also fixed up the images and made it look really sexy. The way this works is

at the very top level we have a global claude agents or gemini.md. And these are userwide rules that apply to all of the projects that you start. And so the very top you'll have this sort of injected and you can set this using a

variety of different formatting conventions and stuff. You could look it up for the specific uh agent platform that you're using. you know, if you're doing claude or something like that, it's going to be stored in a a

tilda.claude slash and then there are variety of other conventions regardless of whatever platform you're using that you guys could also after it's injected the global agents.mmd, it'll then inject the

local cloudmd. And so what you could do is you could have a global cloudmd, okay, that has wide ranging user preferences updated and then a local project.mmd that has specific project preferences updated. And then underneath

you also have uh skills and then your finally inline prompt and I'll touch on the skill section in a moment. But in that way, you can collapse a ton of context and a ton of sort of functionality into very few tokens,

which is important because your build both per token and then the quality of the models tend to degrade the longer the token and context windows get. Next up, I want to talk a little bit about agent skills. And this isn't going to be

an exhaustive resource. If you guys want a super in-depth way to look at skills, definitely just check out my full end toend Claude Code skills course. But agent skills, for those of you guys that don't know, is just a simple repeatable

way that you can standardize workflows.

Now, this is important because large language models are very flexible. So, if you give them a non super tightly scoped task, they'll tend to produce a variety of different results for you.

Well, skills are just a way of basically turning that whole, you know, vagueness, that whole statistical variance into like a really straight line deterministic path where it just does the same thing over and over and over

and over and over again. And so skills are offered now on all major platforms.

We've all adopted them. So you have codec skills, you have Gemini skills, uh, and then you also have Claude code skills and they have very particular specs and they look really, really similar to one another. So, it's worth

me at least going over to high level what they look like. To make a long story short, these are just files that'll exist somewhere within our workspace. These files will have sort of this little title section up here, which

you know is a title because there'll be three hyphens at the top and three hyphens at the bottom. Inside of the file, you can give it a name like PDF processing, a description like extract text and tables from PDFs. Uh, and then

you can even do licenses and metadata and so on and so forth. I don't actually do any of this stuff. my skills are almost always just name, description, and then maybe some optional uh uh tools that I could use as well. Okay, so I

just want to give you guys a couple of brief examples. I'm just going to go over to anthropic um skills because they have a bunch of simple ones here that we can use just to gain some context. I'm going to go over to the skills folder

here and then click on I don't know, let's do algorithmic art. We'll go skill.md because that's the file. And as you guys could see here, um, we have, if I click on the raw, you guys will see we have the exact same format that I showed

you guys earlier. So this is a skill that creates algorithmic art using a particular library. And what's cool is it basically guides the model through the same thing every time to get very, very similar algorithmic art generated.

And you can see this is a pretty long skill. There's a lot going on, right? So what I'm going to do is I'm just going to copy this whole thing and show you guys how this works. In this way, we can copy and paste different um standard

operating procedures to different models and then get highquality results. So, I'm going to go over here and then, you know, just because this is a oneshot prompt, I'm just going to feed all this in. And I'm going to have this model

actually create things according to the skill spec. So, it's doing some thinking. And now it's asking me what do we want to do with it? And I'm going to say yes, save as skill, then run. And then I'm going to actually have this

like produce some sort of cool algorithmic art. Now there's no template file or anything like that. So it's actually going to go through the whole process. It's going to create both the skill directory which we can find right

over here now called algorithmic art.

And then it's also going to create like templates and a bunch of other stuff as well. Okay. And our algorithmic art flow is just finished up. So I'm actually just going to open this so I can take a look at it myself. And we have it. There

it is. This is now creating algorithmic art. As you guys could see, we have particles and so on and so forth. I'm just going to significantly decrease the number of particles. Maybe change the noise scale and the turbulence. Actually

move this around. And as you guys can see, we we we are actually producing a tremendous number of particles here.

This is this is actually like rendering them directly in my browser, which is nuts. Um, so this is indeed algorithmic art. It's it's really cool. Super sexy.

I'm a big fan. I don't know. I mean, it looks kind of like hair, but what are you going to do? I'm just going to regenerate a bunch. Maybe change the accent colors. Okay. Maybe we'll have this as my accent now. Blue. And then

the background will be kind of this. And I don't know, my cool accent will be kind of like this. There you go. That looks pretty nice. We can now kind of just create new ones as we want. And then we can also just completely

randomize them over and over and over and over and over again. And you can see it's actually still doing some design in the background as we go. So I'm just going to change the number of particles to really low. And then I'll just

redesign this over and over and over and over again.

And I should note that like this is not like a, you know, it's not a piece of software I downloaded. We actually just built this. It's just we built this in a much more standardized and you know consistent way which is really cool. So

obviously that's that's what I want. I want the ability to share like repeatable workflows where my agent can build things that other people have validated without me necessarily having just to like copy and paste a piece of

software into my computer. Now remember earlier how I said some models are better at things than others and these few percentage point differences can make a lot of impact at the bleeding edge or the frontier. Assuming you guys

are at the bleeding edge and the frontier and those percentage point differences stack up, then multi- aent MCP orchestration is the pattern for you. Basically here what happens is you let one model type be the manager or the

orchestrator and that orchestrator will take a task and then dole it out, okay, and delegate subchunks of that task to different models. And so what's occurring here is in this hypothetical example, we're using claude code to be

our manager. We then give it some task like hey make me a SAS app that does X Y and Z. And then what it's doing is it's taking my command and then splitting it into a variety of different functions.

There's a front-end task which is delegating to Gemini to build the UI.

There's a backend task which is delegating to codeex to build the API.

There'll be some testing that we need to occur that we need to do which it'll delegate to codeex to do the testing.

Then finally at the end we have claude which we'll collect and then validate the results and then if there are any discrepancies or issues there you know we can loop that back around hypothetically to different models as we

will. And so this is a little bit more of an advanced design pattern and I don't necessarily recommend you guys sign up to a bajillion patterns and waste your tokens that way unless you have to. But I wanted to cover it

because this is sort of like the next generation of model intelligence. It's where instead of just sticking with one, you're constantly querying different models for things that they're a little bit better at. All of this depends on

this idea of a router. And so this router is more or less like a decision hub or like a nexus. When you give it a task where you give it some sort of input, what it'll do is it'll just divide it into different subtasks that

different models are better than other models at. So for instance, if we have like a highle task that has to do with replicating a specific SAS app, you know, and the the model has decided that there's some footage on the internet out

there that talks about how to build it, it'll actually go delegate the video watching step over to Gemini because Gemini is better at multimodality and their endpoints have built-in video understanding. You know, if it

identifies that we need something with a lot of complex reasoning, it'll route that over to Claude. you know, if it identifies that we need some form of sandboxed cloud code execution, it'll do that in codeex because they include that

built in. And maybe, you know, I just wanted to show you guys what an example would look like if you had something that was outside of the three. If you need real-time web data, it might do that with Perplexity or or Perplexity's

computer or something. And what happens is, you know, we build it all by parallelizing this big sweep and then at the very end, we combine it again with this router, which is probably, you know, at least in my case, almost always

going to be Claude Opus 4.6 6 4.7 by the time you guys are reading it. And then that's what ultimately unifies it before maybe doing some additional Q&A bug fixes and agent review which I'll talk about later. Now, all of this sounds

pretty abstract and you're like, "Okay, why don't I just have all of this done in one thread?" So, let me show you a practical way to actually do it. By the way, all the files for this course you can find in the top link in the

description below. What I'm going to do is go back to Claude Code and open up a new session. And then I'm going to select this folder that I've actually already created for this purpose called multiplatform orchestration. Now, as

mentioned, you guys will get everything in the description if you want it. And I'll also run you through how to create it. But for now, what I want to do, I just hide this, is say something along the lines of, "Hey, build me a full

stack app that lets users enter a desired image to generate and then it generates said image." We'll make this really simple because I don't actually want this to take forever. I'm on kind of a time crunch today and I just want

you guys to see how this deals with that problem. Keep in mind in this case Claude which is the model that we're currently talking to cuz it's Claude code is going to be our top level orchestrator. Okay. Now this is going to

plan things out for us which is why it's entering this plan mode. Next what we're going to do is we're going to delegate all difficult tasks um like backend tasks to codecs as well as testing tasks. Then down at the very bottom

here, you know, uh, for anything related to front end, we're going to delegate that to Gemini. And so we're going to build basically an ecosystem here where Claude is shuttling information back and forth between uh, you know, codecs and

Gemini for various things. And as you can see here, it's already starting to ask me, hey, which image generation API would you like to use? I'm actually just going to say um, Nano Banana Pro 2. It's a Google product. Okay, I'm going to

submit that. And now what it's going to do is it's going to decide, hey, how am I going to delegate this work? At the end of it, Claude will give me a plan.

And you can see here that it's decided on backend, front end, and so on and so forth. And what it'll do now is it'll actually dispatch work to Gemini codeex and then itself to fix various integration issues. So I'm just going to

say plan approved. And now it's going to start doing the coding. The way that Claude Code does this is it uses the execute task path for Codeex. And so what's occurring right now is it's just sent this big request into Codex's best

model. Okay. And now just clicking the button in the top right hand corner, we now have a preview. And um in this case, Claude is now reviewing the generated application and doing some self- testing. And so we've built this image

generator app. We've uh asked for a cute cat wearing sunglasses on a beach. This is now passing through to an API that uh Claude Code set up with Gemini for the front end and then Codeex for the back end's help. It's actually doing the the

generation right now and we've generated the cute picture of the cat on the beach looks great to me. The reason why you might want to do this is because well it's kind of twofold. One, you get to parallelize your work as mentioned and

so you get to build the front end u using a model for which the front-end builder is the best. You get to build the back end simultaneously using model by which the backend builder is the best. And then you get to use an

orchestrator which basically ees out a few percentage points increased like reasoning and decision-m and stuff like that because it's able to evaluate the code from both of these things independently without being polluted by

the context window. And we're going to talk more about that specific review pattern later. But um this allows you to e-code, you know, more quality. The downside of this um prompt approach is it usually costs more because now you're

splitting your tokens across multiple models instead of just one provider. And usually providers will subsidize your token usage. Like Claude will subsidize most of its usage on the max plan for instance. Um the $200 a month that you

spend on it is actually equivalent to like $5,000 a month in usage. Whereas when you build via API, it's usually a little bit more standardized and then as a result of that you end up building way more. You don't you don't get that cool

subsidization. However, this is something that people are increasingly using for more complicated infrastructural projects, especially when, as mentioned, a minor percentage point or two difference in terms of

quality is very important to you. And so this is me just doing this in Cloud, but you can obviously use, I don't know, Codeex as the orchestrator if you wanted to build this in Codeex. You could use Gemini as the orchestrator if you wanted

to do this in uh, you know, entirely Gemini. Right now, this is the stack that seems to make the most sense, what people are talking about the most. If you guys are interested, the way that all of this stuff works under the hood

is we basically set up a bunch of different servers that calls and Gemini inside of Claude. And so that's why we see this using the Claude formatting above. It's because the claude is the the orchestrator that's sort of setting

it up initially. And there's also a claude.mmd which describes how it's the manager. You know, you plan, reason, delegate, validate, and fix integration issues. When you break tasks down, break them into front end, backend, and test

subtasks and then delegate things as required. I'm going to include this prompt as well as everything else you need in order to do the same thing down below in the description. But in order for this to work, you will of course

need API keys for various platforms. And in order to get those, you do have to sign up to typically something a little bit different from what we signed up to before. And in order to sign up to those, you do typically need um to go

directly to the platform, create an account, and then set up an API key. So you can see over here, that's what I've done for Claude. And you can also do the same thing for OpenAI and then Gemini.

Once you have those keys, you would just give it to whatever model you want to use to be the orchestrator. And then it would set this whole thing up for you and then be able to reason and then communicate with different models on

your behalf. The next advanced prompting technique is the video toaction pipeline. To make a long story short, up until quite recently, AI agents were forced to learn entirely through text descriptions of stuff. And the reason

why is because multimodality like vision usually uh at least in the context of video was sort of out of bounds. There was just no way that we could feasibly take videos which were millions upon millions of tokens when stitched

together um you know into some text format that an agent would understand.

Well, now agents can learn from the same medium humans learn from. And we do so by combining a little bit about what I showed you guys earlier, okay?

Multi-agent MCP orchestration with this idea of passing requests through the Gemini API because Gemini has built-in support for video now. Basically, uh you know how videos are a certain number of frames per second. Like this video for

instance is 30 frames a second. You could tell if you find a way to to slow it down to like 0.03.

I'll go literally one frame every 003 seconds or something like that. Well, what this model does is it divides videos into one frame per second instead. It then analyzes the images in succession and then uses a form of

descriptive prompting to break that down into very very clear steps. So basically what occurs is you'll feed in something like a YouTube tutorial URL. Claude will receive the URL but cannot watch the video natively. So instead it'll call

the Gemini API. Gemini will watch the full video. Gemini will then extract the step-by-step instructions, format it as like a numbered list that's hyper precise and hypersp specific. The structured steps will return to Claude

via very similar flow to what I showed you guys with the design. And then Claude will execute each using hyperspecific tools. Maybe if you're teaching somebody how to build something on Blender or Figma or something like

that, you just give it access to the toolkit and it does it. Then the final result is the agent will have replicated the tutorial end to end and in that way they can learn from the exact same medium that that we learn. So I'll show

you number one where I got inspiration from this and then number two how to do this for an actual task which in my case is going to be building a simple flow out in a noode tool called NAN. So first the inspiration was Spencer Sterling's

post on X. He said he built an agentic system that taught itself the Blender donut tutorial by watching it on YouTube. It watched the tutorials, extracted the steps, filled in the gaps in its own tooling and completed the

entire thing autonomously. And it's quite impressive to be honest. Um, anybody that's done any sort of 3D design, myself included, will know that like the uh way you learn how to build things in Blender is you watch this one

specific tutorial that shows you how to build a donut. And through this process of building the donut, you learn about like textures. You learn about various shapes. You learn about how to modify them and sculpt and paint and do all

this stuff. So, I made my own donut personally a few years ago. I showed it to all my friends. Then, I promptly never touch Blender again. Well, the issue with knowledge like this is it's obviously extraordinarily visual, right?

In order to really learn something, you have to watch a video. You can't really break all that down into like hyperspecific text instructions unless, you know, somebody were to just like literally go step by step. Step one,

click this button, step two, rotate 283° to the left, step three, do this. So, there's a fair amount of nuance and flexibility there. That's where video learning comes in handy. Human beings learn through video, obviously, but

models have a tough time doing it. And so what we do is we convert all of this into a sequence of steps. We leave some steps a little bit more vague, a little bit more general, let the model have its own um kind of interpretability, and

then give it some way to like screenshot its results to match it up to um you know like the frames in the video. And so this fell here built this cool like workflow building studio. It's sort of like his own main um operating system. I

suppose that's what this is. It's not like an app that he downloaded. It's something that he built. And then he fed in this along with the workflow I'm about to show you to have it actually like build the freaking thing. And it's

communicating with this app Blender using what's called MCP, model context protocol, which is the same thing that we used to communicate with um the various models like Gemini and then Codex earlier. And you can get all that

stuff in the description down below as well. So I have this stored as a clawed skill in video to action um over here.

So, if I open this up and read the skill, you can see here that it actually says, "Extract actionable steps from YouTube videos using Gemini video understanding. Use when the user provides a YouTube link it wants to

learn procedures, extract steps, understand visual tutorials, or turn video content into executable instructions." And so, what's occurring is it'll basically take a video, it'll download it for me, so then I'll just be

able to feed in a YouTube URL, and then it'll convert that into like a highly optimized series of steps that um you know, you would only really know or be able to use through uh the context of like an actual video. And so to

demonstrate what I've done here is instead of using Gemini within anti-gravity, which is sort of the usual design pattern, I thought I'd show you guys my actual stack like what I personally use. I think it's much easier

if you just use the models inside of the tools inside of the companies that made them. But in my case, I'm a very big fan of this anti-gravity uh uh kind of container. Then inside of it, I use clawed code. And so in that way, I'm

actually using a Google wrapper around a claude code or anthropic extension that's communicating with a claude or an anthropic model. If you guys want to replicate the setup, it's as simple as just opening up anti-gravity, heading to

the lefth hand side where it says extensions, downloading the clawed code for VS Code plugin. I know it says VS Code, don't be confused. It's very similar to anti-gravity. Installing it, and then uh you also have to log in

here. After you're done, you will have the exact same functionality that you have in the claw desktop app that I just showed you guys earlier when we built out that little full stack app. It's just you'll have it within anti-gravity,

which also allows you to do things like, you know, organize your files and stuff on the lefth hand side. So, that's my personal stack. You don't have to use it. Some people judge me for it.

Whatever. I like it. It works for me.

Okay. So, um what I'm going to do is I'm going to find a YouTube video that I like and then I'm just going to feed it in these instructions. So, I'll say I want you to use the video to action pipeline on and then I'm going to go

grab an image. And what I've done is I've found a flow that I built forever ago. It's a short video about 21 minutes that shows you how to scrape leads without paying for a few APIs. I'm going to bring that back into my anti-gravity

instance. Then, I'm going to do this.

And what this is going to do is it'll start by invoking the skill. And this is the UX for skill uh invocation. I think that's what it's called in English. Holy crap, that better be what it's called in English. And then um it's now going to

send that over to Gemini, then receive back a list of highly specific instructions that, you know, understand UX, uh I don't know, highlight the colors of buttons and stuff like that and so on and so forth before actually

running it locally on my computer. At the end of it, you'll get a super in-depth analysis that looks like this.

So you can actually see down over here it says here's the hyperdetailed breakdown with literally every single step. I mean like hey navigate over to this thing at 17 seconds. Here's how to do this thing on that and and so on and

so on. So like it'll it'll literally go visually as well and actually tell us what the end flow is going to look like, but then we'll also have just a tremendous amount of context about everything. Um so what we're going to do

now is we're going to feed that in and actually have this control my browser.

So I'm going to open up a new cloud code instance by clicking that little button above. We'll go bypass permissions. Then I'll say use Gmaps scraper deep analysis MD to build out the same N8N flow for me. It's now going to open up a Chrome

DevTools MCP server. It's then going to link that up to the N8N account. And now it's actually thinking through everything that it's going to do using this file as a reference. And now it'll go through and actually control my

browser to do the build. For simplicity, I'm just going to move this over to the right. Okay. And as we see, it just laid out the entire thing from left to right.

So it went through, it then identified what all of the steps were. It then created it inside of its own little conversation thread and then it um essentially generated what's called workflow JSON and then pasted it in. Now

this can obviously interact with my my browser as well. That's what it just did. So it just went to the top and then basically imported this. What it's going to do now is just make some finer final minor changes. I'm going to configure

the Google Sheets node and then we'll be on our way. So, what I'll do is I'll just take a screenshot of this and then paste it in. Then I'll say you're connected. Now, it's just going through and then it's selecting various

elements. So, in this case, it's selecting that little search button.

It's uh mapping the the fields and stuff like that. And then it'll just continue testing this non-stop until I have a working flow. You can see, you know, just kind of I mean, I should be moving this around cuz it's going to get

confused, but you can see that it's um actually gone through and then pumped in like a specific search term. It's it's gone through and basically done everything for me. Really, the only thing left is to do some sort of

testing. You can see that uh if we actually click execute workflow, I'm just going to stop it here so I don't consume anything else. It's actually gone through and literally like scraped Google Maps for us, which is sweet. Uh

and it's just done so entirely by watching the video. So it's entirely like native video understanding and then it's extraordinarily detailed because we're we're dumping it all into a file and then it can just constantly

reference that file. Um it's then doing kind of a combination of like I don't know like ASKI or or text based markup to uh you know understand both the structure at like a micro level and then also like a macro level. Next, I want to

chat this idea of stochcastic multi-agent consensus. In case you guys didn't know, if you were to take one model, let's say Gemini 3.1 Pro High, and if you were to ask it like an idea question, hey, give me 10 ideas to do X,

Y, and Z. Every time you ask Gemini 3.1 Pro the same thing, it'll return a slightly different answer. Now this property some call it randomness but I think the correct technical term is stochasticity which is just where due to

minor statistical variations in the input or in the way that the models work the output is going to be slightly different every time. The reason why this is so valuable is because you can exploit this tendency to get much much

better answers. For instance, let's say I run three times 1 2 and three. The reality is if I run a query that at the very beginning says give me three ideas for X. Okay, on the very first time, okay, we might

get idea A, idea B, and idea C. If we were to hypothetically run this again, we'd probably get idea A, idea B. But just due to statistical variation, there is a chance that on the second run, it won't deliver us idea C at all. it'll

actually deliver us idea D. And on the third run, maybe we do B, maybe we do C, and then maybe we also do E. What stochastic multi-agent consensus is, you basically automate the process of spawning multiple agents, giving them

slightly varied input prompts to take advantage of stochasticity, and then instead of just getting, let's say, three ideas A, B, and C, you get to exploit stats to get all of the possibilities, including ones that might

be a little rarer. the model is less likely to actually answer with. And so in this way you get A, you get B, you can get C, but you can also get D and then you can get E. And so you know if you compare it to just one naive search,

what we've done is we basically almost doubled the scope of the ideation. Now mathematically this is termed traversing the search space. I want you to pretend hypothetically that this like little pie chart here represents all possible

answers to a question. Maybe the question is, I don't know, what's the simplest way to get to 1 million subscribers? Right? This is something that I asked uh my my model a little while ago because I'm interested in

getting to 1 million subscribers. Now, obviously, I'm not just doing what the thing tells me, right? A lot of its ideas are stupid. But if you think about it, if I can parallelize a thousand agents all coming up with their own

ideas, even if on net the average reply or idea is a little bit worse than something I'd be able to do, I still get to run it a thousand times, right? It's like running like uh I don't know like a 90q, you know, it's like it's like

Einstein versus 10,000 95 IQ researchers. It's like well the 10,95 IQ researchers despite lacking the brilliance of Einstein, they'll probably statistically figure it out eventually, right? So um if this whole pie chart to

get back to things is all possible responses, if you just run one search, basically what you're doing is you're only actually getting like a small chunk of all of the possibilities. And so instead what we're doing is we're

actually running multiple searches. You know, one search is going to get this, another search is going to get that, another search is going to get that, another search is going to get that. And and and so on and so forth. And then in

this way, what we do next is we take the answers and then the replies of the model. That should be red and this one should be blue. And then in doing so, we get to traverse significantly more of that search space without actually

necessarily consuming any more of our time. So this can be kind of difficult to understand. And I think I've run out of colors here. uh unless you've done something like this before. But I'll make it really simple by actually giving

you guys a brief demonstration on I don't know some use case or problem that uh I think we'd probably all be able to relate to. Another final benefit is you get to do all this in parallel. So like you know if you think about it if you

were to do one search and then do another search afterwards and then do another search. So for instance let's say you have a query give me three ideas for X and then it gives you three ideas and you're like hey I want another three

ideas and it gives you another three ideas and you're like I want another three ideas. Well, at the end of it, you may have, I don't know, nine ideas or something, but it will have taken a certain amount of time. If the first

search is 5 minutes, the second search is 5 minutes, and the third search is 5 minutes. Well, you just consumed 15 minutes, right? So, instead, what this does is this just copies the idea. Okay?

But then it parallelizes it. So, hey, give me three ideas for X. And then what we do is we do 1 2 and three. And in total, this takes 5 minutes. And then we just combine those three answers back over here. The formal way to do

stochastic multi-agent consensus, at least the way that I'm doing it here, is we'll provide a single question or prompt. Then we'll do slight framing variations of every prompt that we're feeding into the model. And then we'll

feed in I don't know, I'll probably feed in like three or four, five or maybe 10 simultaneously. Depends on how deep you want it to go. And then um what'll happen is these will be instantiated as what are called sub aents, okay? Which

are similar to the main agent, but they operate in their own defined context window. And then all of these will just report back their answers to the parent agent. So this parent over here is basically going to work with a whole

fleet of sub aents and then once they're all done their work, it'll synthesize the answers. And then because what we're looking for is we're looking for like statistical variation, it'll calculate um what's called the mode, which is the

frequency of each answer, and then the median, which is like the average of each answer before ultimately combining all this to give you much better results. One final idea there is this idea of consensus. A lot of models are

going to say the same things. Obviously, some models are going to say things that are quite different. And then finally, there will be outliers, which are wild cards. These wild cards here are potentially brilliant, but they might

only appear like 5 or 10% of the time, which is why we spawn so many of these agents that we can actually like farm these wild cards. We can we can milk them like cows. And then in that way, you can have the best ideas coming from

these these fleets of agents. Um, and then also save a lot of time in things like product ideation. I don't know, man. Keyword search, titles for for for content. At least that's what I'm using it for. Or a variety of other things.

Hell, research inventions. I'm sure Anthropic and and Google and OpenAI probably have fleets of models that are doing basically this exact same thing behind the scenes constantly. Let me actually show you guys what this looks

like in practice. I'm just going to zoom way out of this and close a bunch of these so you don't have to look at them anymore. I'm going to spawn a new Claude code tab over here on the right. And what I'm going to do is I'm going to use

the skill that I've set up called stochastic multi-agent consensus. So opening this up so you guys could read it. What we're doing is responding n agents where n is just the number that you specify with slight framing

variations to independently analyze a problem then aggregate results by consensus. We use this for decision-m ranking things strategic analysis or any problems where you want to filter hallucinations and surface high variance

ideas. So hypothetically let's just say hey I've struggled a lot with finding any traction on Tik Tok whatsoever. I've built up a bunch of accounts and I can't seem to get more than like a thousand views per Tik Tok account. I'd like you

to use stochastic multi-agent consensus to help me come up with possible candidate ideas to solve this. I'm going to feed this idea in. Okay. And this is a real idea. Actually, we are struggling to get uh traction on Tik Tok for

whatever reason. We got 450K followers on Instagram. No problem. But, you know, the second we move things over to Tik Tok, we're just not really getting too many views. So what it's going to start with is it will spawn 10 agents all

independently analyzing my Tik Tok problem and every one of them will get slightly different analytical framing to maximize the diversity of ideas. Just going to zoom in here so you guys could see this. But we now have a conservative

analysis. So Nick Sarif has 287K YouTube subscribers. You know um his YouTube audience is primarily professionals.

Here's a bunch of information about him.

He has a small team. here's how he's doing things and and so on and so forth.

This agent over here says, "Hey, I want you to assume limited time and budget." This agent over here, I want you to only focus on what is measurable and provable. This agent over here, you know, I want you to think about it from

the end user and viewer perspective. And so what we're doing is we're basically taking advantage of the parallelizability of models, not necessarily the base intelligence. So the intelligence is obviously important,

but like we care more about like scanning and searching through a space of all possible solutions really quickly. And then at the end, we're going to converge all this back with our parent agent. Now, once all these agents

have turned green here, if I open up this thinking tab, you could see that it's now combining all of the information from each individual one.

So, there's a bunch of uh suggestions saying, "Hey, you should try fresh account. You should try device reset.

You should try clean fingerprinting.

Hey, you should try Tik Tok native hook reformatting. Hey, you should do duets with existing creators to take advantage of the fact that you're probably bigger.

Hey, you should do a series format, high posting frequency, and so on and so forth." And then you have some disagreements here as well. And this disagreements might be paid Tik Tok spark ads. Only one out of 10 agents

suggested something. You know, in this one, um, they recommend using shorts.

But then in this one, they recommend using a micro topic focus to build authority and audience clarity. You know, I'm not going to sit here and pretend like all these ideas are the bee's knees. Not all of them are

capturing lightning in a bottle, but you run this thing long enough and you'll see eventually you will get some pretty good ideas. And the ideas will be consensus ideas like the idea of a fresh account, but it'll also be kind of like

outlier ideas with painoint framing, paid Tik Tok spark ads, niching down your account identity, crossosting your Instagram reels to YouTube shorts first.

I mean, there there there are a lot of possible ideas right now. It's opened up this consensus report, which I can visualize for you guys by clicking this button. And you can see here it's now saying, "Hey, here is the context. Tik

Tok growth stalled at 1K views per account across multiple accounts despite this massive YouTube subs and 450,000 followers with almost 5 million reals views a month. And then here um this orchestrator now summarizes it and says

hey every agent independently identified Tik Tok native hook reformatting is really critical. You know Instagram is a little bit different from Tik Tok hooks.

Content optimized for Instagram will systematically fail Tik Tok's cold start test. So you actually have to restructure it if you really want to crush. Same thing here. fresh account, clean device, fingerprint. I mean, there

is just so much context here, it's not even funny. And so, the reality is I would have come up with these ideas at some point, but I basically got to put, you know, a genie in a bottle and then have 500 genies simultaneously solve my

wishes at 100x speed and then aggregate all results for um you know, I don't know, probably like three or$4 dollars realistically in terms of tokens. You also had a couple agents that said, "Is Tik Tok even worth it?" And uh I think

that's a really good question to ask because up until now, I really didn't think it was worth it. And so, in general, anytime that I recommend you have a strategic decision that you need, you can make a quick one-time tradeoff

of money for analysis by spawning a bunch of agents, all with slight prompt variations, and then collecting the rankings reasoning to build this consensus map document. And from here you can figure out your consensus items,

your divergent items, and then your outliers. And you know, if they're consensus items, well, odds are probably because a lot of models have thought it's a good idea. You should probably do it. If there's some divergent items,

well, you should probably like reason about these quite a bit before deciding on whether it makes sense. And if it's like an outlier item, if there's only one out of 10 agents doing it, well, it can either be a brilliant idea, in which

case maybe you should give it a try, or it might just be a hallucination or some BS, in which case you don't. And so what this allows you to do is execute with high confidence. Thank you very much AI for drawing that cute little that is a

huge fist. That thing would be terrifying in real life. Um you know this lets you scan a large portion of the search space in a very short period of time. And uh yeah the actual way that you build it is very straightforward and

I'll run you guys through what all that stuff looks like um down below in the project description. So just like stochastic multi- aent consensus allowed us to scan large amounts of search space in a short period of time. What we did

is we independently delegated work over to agents and had them uh do things for us. So too can we take advantage of this same idea but in my opinion get even higher quality results through this idea of agent chat rooms. What agent chat

rooms are are where instead of you know parallelizing all the work and having all these agents try and independently solve problems what you do is you give all of them slightly different personalities and then you have them all

debate with each other about these problems. And in doing so, they tend to deliver much higher quality responses because they're just like they're they're a little bit spikier. You know what I mean? They're not just like a

generalized idea, which I'll visualize with like this interface, but you know, because they're they're butdding heads with another um eventually the ideas get really nuanced and really high quality.

And so, um whether or not you visualize things in that way, that's personally how I think about things. You really get to carve out all the tiny little nooks and crannies of an idea when you debate.

And so, here's a brief little visualization. We start with a problem or a prompt. We feed it in to let's say three agents here. Agent A, agent B, and agent C. All three are given the same document called chat.json. And then what

occurs is they basically cycle through a debate sequence where agent A says something, agent B says something, and agent C says something. And, you know, if you do this naively, the results will probably be pretty low. But if you, I

don't know, force a little bit of a spark where every agent has a slightly different opinion and they're not afraid to like state their opinion, um, they'll challenge each other's assumptions, they will significantly improve the

probability that you catch errors. And then this chat.json ends up being quite a valuable resource because it also shows like problem solving and stuff like that. You can then give that to an orchestrator and ultimately receive

higher quality output at the end. And so it's sort of similar to what we had earlier, right? It's just instead of this operating um in parallel lanes, what these agents are doing is they're actually talking back and forth with

each other. And so they're actually capable of having these conversations.

And I mean like I I just want you to pretend we actually spawn 10 agents.

Agent one would be able to communicate with agent two, but also agent three and also agent four and also agent five and also agent six. So like the total number of paths and um potential like communication I don't really know what

you want to call them like like vectors um goes up like crazy and these agents ultimately assuming that the idea is an absolute BS do end up at the end of it like quite quite differentiated u in their ideas and their opinions. So to

show you guys what this looks like I have another skill which is just a repeatable workflow to be clear where I have this model chat. The description here is to spawn five claw instances on a shared conversation room where they

debate, disagree, and converge on solutions. They use roundroin turns with parallel execution within each round for simplicity. Then they trigger on the model chat, multimodel debate, or something else. So I have a bunch of

contexts down over here and you guys can grab this file for yourselves. What I'll do is I'll actually just pipe this into model chat. Okay, great. Use model chat for a similar to really work through this idea. And now it'll spark this

model chat skill which will then have them all dump shared context into a little chat.json which I'll show you guys when it's done. Okay, so the debate has now concluded after these five agents had this conversation. Okay, we

can actually see the the the chat conversation as well by going down here to this model chat. Let's go latest and we'll go conversation. Um basically what's occurred is we've given it a topic to talk about and then we've

assigned a systems thinker, a pragmatist, an edge case finder, a user advocate and then a contrarian to the task. So first of all the systems thinker begins, the pragmatist replies, the edge case finder goes, the user

advocate goes and so on and so forth.

And you can see each of them are um pretty pretty interestingly suggesting uh various approaches. So the user advocate says, "Let me push back on something that challenges the consensus has glossed over, which is the clean

device plus fresh account fixes fingerprinting is the problem. There's a simpler explanation nobody has stress tested. Nick's content format is fundamentally mismatched to Tik Tok's cold start algo." And so these are sort

of arriving at similar conclusions despite the fact that uh you know we instantiated this separately. And then if we check out the synthesis, we can see that all of them have agreed that we need to run some diagnostics that hook

reformatting is necessary but sufficient. the high volume posting blitz two to five a day is wrong. And then fixing the IG YouTube pipeline immediately is important regardless of the Tik Tok decision. This is something

that I guess I got contact from one of my other files because um basically despite the fact that I have 450K Instagram followers, a very few of them are converting to YouTube subscribers and a lot of people a lot of models as

well are suggesting that the reason for that is cuz Instagram is really blocking outbound links which I think is actually fair. But then uh there are a lot of you know disagreements as well. So a lot of people say, "Nope, Stitch Duet's stupid.

Tik Tok versus IG pipeline is an eitheror. Device fingerprinting might not be the issue. Maybe it's content mismatch." Right? And uh there are a lot of insights that because we were able to sharpen our opinions via debate, these

agents got that the previous model runs through stochastic multi-agent consensus did not. So maybe we're looking for saves, not completions. Maybe there's just no category online yet. Although this is not true, if they had the

ability to research, they probably would have figured this out. Maybe it has to do with emotional moments. And then here it even gave a recommended execution plan. So, as mentioned, you know, I wouldn't rely on agents for strategic

advice at the moment, but I would certainly not be opposed to trading a little bit of my money for a bunch of my time back and at least ideulating through the lowerhanging fruit. If you run enough of these cycles, you will

find pretty intriguing and interesting outlier ideas. That's just how statistics works. So you guys can get all this down below in that document.

The next idea I want to talk about is this idea of sub agent verification loops. To make a long story short, where previously we took advantage of parallelization, we're going to take a step back now to sort of serial um

processing. But when an agent works really hard to accomplish a task for you, it usually gets pretty biased in that it believes that its path was the best. And the reason why is because, you know, it just spent god knows how much

time, energy, and compute cycles building your app or putting together your workflow or doing your taxes or whatever the hell. And because of that, you know, series of like design decisions and then issues and bug fixes,

it's just very consolidated in its opinion that the way that it did what it did was the best. So if you were to ask that same agent, hey, can you make this better? A lot of the time it'll look at it and be like, well, no, I did a pretty

good job. I don't think there's any way to do it better. However, instead of just giving that agent back the entire context and saying, can you do it better? A much smarter thing to do is to take all of the um outputs, not the

reasoning, then give the output, aka your code or your workflow or the results of your your accounting to another agent and then say, "Hey, is this right?" Because now that second agent can evaluate purely based off

output. It doesn't actually have to deal with evaluating things based off the reasoning or the intent. And so your um work can end up being a lot higher quality as a result. So here's a quick example using like a coding thing where

uh we wanted to build a rate limiter.

What'll happen is our first agent will implement and write the first draft of the code. This code output will pass to a reviewer agent. Now the reviewer agent is spawned with fresh context, meaning there's no tokens that are polluting its

window and a zero bias. And what it does is just like objectively speaking, you ask it, is this thing correct? Are there any issues here at first glance? Any ways you could simplify this? Now, because it's treating this just like

it's treating a random snippet of code it finds on the internet, you know, it it has no opinions. It has no inherent like desire to claim, well, this is the best way because I spent all this time, energy, and research figuring it out.

And it'll be able to to look at things with, you know, those fresh eyes. From there, if it finds issues, the idea behind sub agent verification loops is it'll list those issues and then pass the suggestions to a third agent called

a resolver, which has zero context about any of this stuff as well. And so in this way, an implement reviewer resolver loop can get significantly higher quality results than just one agent doing everything simultaneously. If

there are no issues, everything's approved, we're good to go. Um, otherwise it resolves, we do some testing, and then we get the final verified code output. Are you guys noticing a trend here? Basically, all of

these like advanced agent foundation uh advanced agent prompting techniques ultimately circle back to having multiple agents working in parallel. And it's really interesting because like the way that agents work themselves is they

already do work in parallel. You know, a few years ago, um, agents were basically just one statistical model and you would ask the statistical model to help you complete the the the sentence or whatever and then would give you the

most likely next token and then would rerun over and over and over again until it did that. Well, a few years back, um, people started introducing this idea called a mixture of experts, which is instead of just having one model, what

you do is you actually send the same thing to like three or four models, you average out the statistical probabilities of every word and then you just pick what they all converged on.

Very similar what I did there with stochastic multi-age consensus. And so this mixture of experts is sort of like the base foundation that resulted in a really big improvement in large language model accuracy among other things like

post-training and RLHF and and and stuff like that. But what's really cool is all of these frameworks basically do the same idea. You know we we treat these mixture of experts now as themselves models and then we prompt them with each

other. We do them in parallel and then integrate their answers like stocastic multi-age consensus. We have them debate against each other like with model chats. And now what we're doing is we're basically having them correct each

other's work like with sub agent verification loops. So all of these are just try uh trading off the same core foundational like features of models which is that at the end of the day they're statistical machines. And so the

more of these statistics that you can I don't know average out the closer you get to the reality. Another way of thinking about this is if the implement agent has already spent 200,000 tokens accumulating all that context, it'll

literally remember every wrong turn and every dead end. It'll have a sunk cost bias. It'll say, "Well, I wrote this, so it must be right." And in a way, it'll be blind to its own mistakes. When you pass it off to this super nerdy looking

reviewer agent, it has a fresh empty context. It'll only see the output, not the journey that we took to get there.

No emotional attachment, although I think this is unnecessary at theorphization. And it'll catch what the reviewer missed. So, uh, let me show you guys how this actually looks like in practice. Here I have this app that I

developed a while back for a video on vibe coding, and you guys can check that out in the description if you're interested. It's where I basically put together a full endto-end system that allowed you to um, design and then

syndicate a bunch of content. So, you know, this is just some app, right? This app, I don't even know if it's fully functional. Okay, no, it isn't because I had to turn it off. But hypothetically, there's a big code base here, right? And

so what I want to do is I want to use this app to show you guys how an un um biased code reviewer would take a look at the code that a previous agent had written, in this case Gemini, and um and improve it. So what I'm going to do is

I'm going to go find this repo. Okay.

And I found it over here. It's in the Splinter repository. That makes sense.

I'm just going to open up a new Cloud Code instance. And then down over here, I'm going to say I'd like you to use, and I just need to make sure I know what the skill is called.

agent review on the Splinter repo. It's let's just say folder. It's in the parent folder so that it knows where this is. That way I can still execute it within this um business uh workspace which I found a much better way of

organizing things. And while it's doing that, I'm going to open up the skill.md.

So what the skill.mmd does is it spawns sub agents to review, simplify, and verify output. It uses after completing many non-trivial implementation tasks and it triggers on the words review this agent review self-review or you know

slag agent-review and you can see it's already doing this. It's um spun up a sub agent called review splinter codebase. And what this does is it reviews it for four things. Correctness, edge cases, simplification and then

security. Now like do I know how to do all this programming under the hood? No, I don't. But these agents certainly do.

And so we can take advantage of that by having an agent with zero context. this one here, review that entire workspace um sort of independently and objectively. And now it's doing a bunch of reading and it's going to integrate

that with the suggestions of this model to give us a much higher quality output.

All right, the Splinter code review just finished up and we found 22 issues across the codebase. There's some critical ones here, some high issues here, some medium issues here, and then some low issues over there. Now, it's

asking me if it wants me to start fixing any of these, and I'll say absolutely.

And the whole idea behind this now is we're we're capable of looking at this completely objectively, you know, like I asked the initial model Gemini when I made the uh the app in the course like multiple times, hey, are there any

issues here? Hey, are there any ways to make this better? Hey, what do you suspect is a problem? And just couldn't find it because it was so polluted by its own biases. Now another model can and it's very similar to like peer

review in like academic um circles. It's not that like you know you're dumb for coming up with this codebase like how dare you. It's just that as you work on things more and more and more, you tend to see things a little more narrow and

more narrow because you've explored a bunch of other possible paths. And the reality is the fact that you explored those paths and those don't work don't necessarily mean that if somebody else explored one of those paths, it wouldn't

work either. And so this is just a way of remaining as objective as humanly possible, which is obviously a very valuable thing to do when you're doing things like creating applications, code, um, you know, sales, marketing, and all

the various things that AI agents allow us to do. Next up, I want to talk a little bit about prompt contracts. For those of you guys that don't know, earlier on we chatted a little bit about a definition of done, right? Well, vague

tasks, aka tasks that don't have clearly defined definitions of done, are basically the number one problem nowadays with what I would consider to be people's like disillusion with AI agents. Like when a total novice starts

using AI and then they dive into some agent coding platform and then they just say, "Hey, build me a Netflix 2.0. make me a million dollars, make no mistakes.

Um, because of their extraordinarily poorly defined definition of done, because they're poorly defined goals, because they don't give it any constraints, because they don't give it any failure conditions, uh, that model

is just not going to do any any get anywhere near as high quality and end result as if they did just follow a simple little uh, step-by-step process.

And so the step-by-step process obviously you could learn, but you could also just like hardcode it as a skill somewhere in your workspace or as uh you know something in your cloud NMD and then just force your model to always

have this information before you proceed. And so for instance, if you give it a vague task like build a rate limiter, okay, it'll do pretty poorly.

But the whole idea behind a prompt contract is you basically make the user who puts in a request like this sign a mini contract and just say, "Okay, cool.

The contract is, you know, here's what your goal is. Here what your constraints are. here's what your format is and here's what your failure is. Are you good to go? If the answer to that question is yes, now the model has

actually gone through the step of defining your goal, your constraints, your format and your failure. And so all of your definitions are done, all of the various uh kind of technical spec requirements here are much more laid out

and then the model sort of has a lot easier of a way of going about things.

And so this is very similar if you guys are aware um to like this idea of scopes.

Now I, you know, I run like a freelance education platform, like an AI automation agency education platform.

And so scopes are a really big part of like a successful project. Um, and so I teach people how to define like really precise and concrete scopes. Uh, whether you're doing, you know, a small project for a client or working with some large

enterprise business or something like that. And like a real real common issue is scopes just tend either to be way too vague and so people don't actually clearly define them or they end up way too restrictive in so far that people

you know in a in an attempt to counterbalance the vagueness. They end up going like way too specific and then the scope ends up being like so restrictive that it's like you know you're a slave to it and you can't

change anything. And so prompt contracts sort of help you navigate the the thin line between too vague and too restrictive. And it's very similar in nature to like giving a contractor a task and then the contractor clarifying

with you before they actually do the task which I think you know is clearly a consequence of agents pushing all of us more towards like management style positions where we just manage the inputs and the outputs of these things.

So a big fan of defining these clearly.

So what does this actually mean in practice? Well, there's obviously a million and one different ways you can define prompt contracts. The way that I've decided to do so in this demonstration is through a skill called

prompt- contract. And so basically before implementing any non-trivial task, the skill forces you to generate a structured prompt contract with goals, constraints, the format of output, and then failure. So the idea here is you're

treating it just like a spec or a scope of work. Any task that produces code or some configuration settings or something like that needs to go through this process. And then this model will sort of selfanalyze the request before

drafting a four section contract and then presenting it for approval. This is almost uh similar in nature to like the plan mode that a lot of these um agent platforms now have. Like in cloud code for instance, it can enter plan mode and

give you a brief little plan and have you approve the plan before it proceeds.

It's just this formalizes it as a contract. And no, you're not signing your life away with cloud code when you do this. Um, but you know, it's a simple and easy way to make sure that you get more repeatable and consistent and

accurate outputs every time. So, why don't I actually do this? Use prompt contracts to define this task. And then I'm just going to pretend that I'm giving it a really simple query. I'm just going to say, I want you to build

me a beautiful site for leftclick.ai.

That's my um agency. So, what it's going to do is it'll begin by invoking the skill prompt contract. And I mean, beautiful site is such a subjective term, right? right? I mean, like, what the heck does that even mean? And so,

the model is going to be essentially forced to ask me for more context on what constitutes a beautiful site to me.

And in this way, we'll get a much higher quality site or app or whatever the hell at the end of it. Likewise, you could do this with any business task as well. It doesn't just have to be like a design task. Um, you could set up a prompt

contract for, hey, email these 45 people. And it could ask you like, oh, like what spec, you know, specifications do you do you want to confirm that they're emailed? And what do you want the emails to say? And what's the goal

of a successful thing? and like, do you have any failure parameters? If we only email 44, is that okay with you? Right?

It basically forces it to be a lot more clear and then concise. So, what's happening now is it's gone through, it's actually accessed leftclick.ai, that's my current website, and then it's um getting a bunch of screenshots and stuff

like that. And the reason why is because it's attempting to build up context for the prompt contract. So, its first step was to analyze the request, right? What it's going to do is it'll identify what done looks like. It'll identify some

implicit assumptions. So, what am I about to force the model to assume without being told? Well, obviously an assumption is I already have a website, right? And so, it's going to go through, take pictures of my website, and see,

well, if Nick wants something different from this, why? And then, it's going to sort of make its own judgment to that end. And now, it's actually giving me the contract. So, the goal is a single page marketing site for leftclick. Here

are some constraints. You know, we want smooth scroll animations under 500 lines of HTML. The format is this. There should be these sections. subtle animations fade in on scroll hover states. A failure is if it looks like a

generic Bootstrap template. A failure is if it's broken on mobile. A failure is if the animations are janky. The failure is if the file exceeds 500 lines. So, I actually really like this prompt contract. It's really simple and

straightforward. So, I'm actually going to say go ahead and build it. But what's cool is, you know, we're now actually having a conversation about this. We're actually agreeing on, you know, what the end result is going to be. And this is

actually really similar in nature to the other thing that I want to talk to you guys about which is um kind of related and orthogonal to prompt contracts although it is a little bit different.

And this is called reverse prompting.

Now reverse prompting is in a similar vein a mechanism used to clarify the quality of a prompt and improve the probability that it ends up okay. And basically the way that this works is instead of just like forcing the model

to give you this contract and having you sign off on it, it it takes it one step further. it actually forces the model to ask you some clarifying questions ahead of time. So rather than just give you a spec sheet and say, "Okay, we're good to

go." What reverse prompting does is it um has the model ask you a bunch of questions that you maybe didn't even think that you had to answer, the model then takes all bad context and then feeds that into a prompt contract later

on. Okay, so step one is when the user gives a task to an AI agent. So I don't know, this is like a website, right?

Step two is the agent asks five clarifying questions back to the user before starting. Step three is when we answer and then the agent builds the correct thing on the first try. So significantly improves one-shot

potential. And then if we didn't have reverse prompting, there'd be a lot of like wrong implicit assumptions here which would result in, you know, the probability of a oneshot, which is just when the agent does it in literally one

request uh going down quite a bit. And so similarly, I also have a reverse prompt skill over here. And so if I go to this reverse prompt skill, you can see the way that this is set up is before implementing any non-trivial

build, ask the user five dynamically generated clarifying questions to surface non-obvious preferences, assumptions, and constraints. So when to trigger before starting the implementation, step one, analyze the

request, figure out some stated requirements, implicit assumptions, some decision points, failure modes, and taste dependent choices. Right? And so likewise, if I instead wanted to build, let's say something for

build a beautiful site for 1 second copy, which is my old content writing company, which we just had to shut down a few days ago. U as you guys can imagine, content isn't super in these days.

Oh, and then um use the reverse prompt skill and chain it together with prompt contracts after. What you could see is we're now engaged significantly more than we were before. Before I just say, "Build me a beautiful site." Probability

that it gets what I want right on the first try. Pretty damn low. What it's doing now is it's asking a bunch of clarifying questions to confirm whether or not, you know, this site is as I want it to be. And then after I feed it back

that information, it'll then take that and use that to construct essentially that that prompt contract that we had before. So here's what the conversation looks like. What's the primary goal of the site? Brand credibility,

salesfunnel, lead genen. You know what I want is just brand credibility. Should it be a single static page site or should I build it in some other framework? No, I wanted a simple site.

What's the vibe? You know, it's AI content writing. You know, should I do a clean modern SAS aesthetic? Think linear versel? Do I want something different?

Yeah, I want like linear but white. You know, should I generate the copy from context or use some placeholder content?

No, you're cool. You can generate it from here. Now once we've clarified everything, what this model is going to do is use all this information to outline the prompt contract using the prompt contract skill. And now you can

see it's invoking this skill as well.

And here we have a contract. It'll be a single page static site for 1 second.

Copy linear weight aesthetic 5 seconds deploy ready. Here's some constraints.

Here's the format. Maybe I don't like the format. Maybe I don't want it inside of active, you know, I want it somewhere else. Uh but anyway, in in this case, maybe I want to look good and build it.

Now, just to show you guys an example of how much higher quality we can get when we actually do this, this is the um website that uh it just built for us.

I'm just going to refresh this puppy and take it to a new window because it gets cut off that window. This is here. We have those cool sexy animations. As we scroll down, we also have some information. Um it's it's light theme,

right? We have these really minimalistic requirements here. Information about myself, some services page, words from happy clients, and then ultimately like a CTA. And so, you know, the reason why I was able to get much closer to what I

wanted, which was a minimalistic white high-end aesthetic is just because, like, you know, I I had it outlined in a contract. As I'm sure you guys can imagine, you can employ the same approach for whatever the heck you want,

whether you're building a site or you are, you know, selling to people or you are doing some sort of bookkeeping or accounting. It's all just about uh building out a very strong definition of done. And the model can assist you with

this. You don't actually have to sit down and laboriously write it all out yourself. And that takes us to the initial demo that we started with which was the multi- aent Chrome MCP manager.

Now basically at the very beginning of this course you didn't understand how you know one agent could spawn a bunch of other agents. You didn't understand a lot of like the parallelization plays.

You also didn't understand that uh you know you could have agents actually chat with each other and communicate. You didn't understand the idea behind using one agent to verify the work of another.

you didn't understand the idea behind delegating to multiple different types of models. What's really cool is the multi- aent Chrome setup that I showed you guys where we had, you know, five or 10 agents all operating independently in

their own browsers, in their own workspaces. All of that just feeds off of this this idea or this concept um of, you know, agents increasing their level of communication with other agents. And so essentially if you think about this

logically, you know, if I were to do this uh with like a single agent, so let's just say one agent, you know, it's not actually rocket science to have one agent use a browser these days. There are built-in skills called MCPs, model

context protocols basically that you can just pipe in and immediately connect to and it can do everything for you. Okay, it can it can launch Chrome and then it can control things on the page and whatnot. It can do that. So, you know,

the issue is it just takes a lot of time. We'll receive the target URL.

We'll launch Chrome via the DevTools MCP. We'll navigate to the website.

We'll take a screenshot and you know in my case this over here was like um specific for me which was just page or rather form fills. After that we'll identify the form extract the form fields generate a personalized message

fill the fields and then click submit.

Um but you know this is still something that's occurring linearly and because of linear constraints you know unless you are using uh I don't know like a Gemini flash model or you're using fast mode and burning through your clawed token uh

usage limits this is going to take a fair amount of time. This process over here literally to just like launch the browser could take 5 seconds. This process to navigate to the website could take 5 seconds. Taking a page screen

check could take 15 seconds. Identifying the contact form could take a minute.

You know, if you stack it all up, basically what's occurring is this whole process here might take literally 2 to 3 minutes per form if you're operating naively using a slower model. And if you're operating non- naively, if you're

using a smarter model, then obviously you have to weigh that against cost and and and token usage and stuff like that.

So, I don't know, let's hypothetically say in my case, I wanted to reach out to uh you know, 1,000 people. Well, if it takes me 2 to 3 minutes to form, that's 1,000 * 2. That's 2,000 minutes, which divided by 60 is like 30 hours or

something like that, right? That's a very long time. It's going to take me a whole day. So, instead of just doing one agent, what I'm going to do is I'm basically going to give every agent its own both Chrome instance and then even

its own workspace and then open up its autonomy so that it can make um some advanced decisions to basically help it build its own tooling if it needs uh in order to like navigate website pages or whatever. Now, what this is going to

look like it's pretty similar to um our previous uh you know stochastic multi- aent consensus prompt where basically we have a user up top. Okay. And this is us. And what we're going to do is we're going to give all the context about our

task whatever it is that we want you know fill out a form or I don't do some lead genen to an orchestrator agent which um in this case I'll do claude and we'll just do opus which uh in my case is going to be 4.6. Maybe in your case

it's a better model. And then what that'll do is it'll spawn and set up, you know, however many agents we want in separate windows. That'll then all in parallel navigate to the site, find the form, fill the fields, and then do the

submission. And so basically, instead of it taking 2 minutes per form, what we can do is we can actually submit, you know, however many forms. So I don't know, let's say we have like 10 agents, we'd submit 10 forms in the same amount

of time it took to submit one. So maybe for us it'll be 120 seconds. And then what we do is we just we just increase this as necessary. I mean I could theoretically have 500 operating if I had the computing power. So you know if

um previously it was one form in uh what did I say 2 minutes and that means the form per minute rate is like 0.5 forms a minute right but now if we spin up 10 and we do 10 in 2 minutes we're up to five a minute. If we spin up I don't

know 100 and we're up to 50 a minute.

And you know, if my goal was 2,000 a day and we're at 50 a minute, then obviously 2,000 divided by 50 means we can get this whole thing done in 40 minutes. And you know, depending on the the the list and whatever the heck you got, obviously

the constraints change, but um this is how you can have multiple Chrome instances operating simultaneously it navigating the website and stuff like that. What I have here is a skill called multi-- aent-chrome. And again, this is

something you can implement using whatever um context framework you want, whether it's a skill, whether it's like a claude, Gemini, or agentmd, whatever the heck you want. What this basically forces it to do is to orchestrate

parallel browser automation using multiple Chrome DevTools MCP instances.

And this is used when a task requires doing the same browser action across many targets simultaneously. So some good examples are submitting forms, filling apps, scraping pages that need JavaScript rendering and and whatever.

And so what's occurring down here is basically we have a tople business workspace which is sort of the folder that I'm in right now. And this actually interacts with a bunch of Chrome agents which all have their own little MCP

servers their own little um claw.mds and so on and so forth. And then they all communicate with a centralized chat and if they run into problems on websites if they have any reports they want to give basically what happens is this

orchestrator just checks the chat every 30 seconds or so. Okay. So the very first step is it determines how many agents are needed. Then it launches all the Chrome instances. It resets the chat file because uh you know previous runs

may have that. And then you can see how every individual sub agent actually monitors its own um task list by basically just pumping things into a chat. This is one of the simplest and easiest ways of getting this specific

design pattern done. As mentioned, you guys can get this down below if you want, but I'm just going to give you guys a simple example, which in my case is going to be just finding Vancouver rentals because I'm, you know,

considering getting a rental um down there. And so, you know, rather than have it give you crappy results, this thing can actually navigate like Craigslist, Facebook Marketplace, Kijiji, whatever the heck you want. Uh,

and the the specific script is right over here. So, hypothetically, what I'll do is I'll just open up a new window.

And then I'll go over here and then I'll write uh I want to find a rental in Vancouver. Needs to be 15 minute walk from the Granville Sky Train station downtown. use multi- aent Chrome to navigate through sites and give me high

quality sleek places under 2.5 let's say 2K to 2.5K other restrictions like one bed one bath reasonably near the water needs AC built in okay so I'm giving it a highle um you know piece of instruction and sorry what

meant to do is actually do prompt contract after this. And now I want it to give me like a very clear contract.

So it's going to give me a list of 5 to 10 rental apartments. Why don't we say 20 rental apartments? And then I'll say 1.2 km is fine. We'll say near water, south of Drake or west of Bard. Okay, I'm just going to make some changes

here. And then I'll say that sounds pretty good. Go for it. And now it's going to actually launch the multi- aent chrome scraping. So it's then going to invoke the skill. I'm just going to keep my hands off. What it'll do next is

actually spawn um four parallel Chrome agents, one per rental site. So, it'll determine that there are four rental sites that it's going to be running through. And it'll just have one Chrome instance sort of do everything there uh

per site. So, now we have the four instances. I'm just going to open this up here. Open this up here. I'll move this one down over here. I'll also move this one down over here. Obviously, you could use an approach like this for

pretty nefarious purposes. Um, so you do have to be cognizant of that that a lot of people and websites are probably um, you know, they're looking to verify whether or not you are a person. And so there are multiple things you can do to

get around that if you so wanted to, like using custom um, browser fingerprinting and whatnot. And I think that's a story for another course because I don't really want this course to be accused of just showing you guys

how to spin up like 500 Chrome instances scraping all sorts of illicit information on the internet using unique browser fingerprints. But uh that stuff is definitely possible and there are probably like a lot of people doing

stuff similar to this right now. They're just way farther ahead in terms of their uh you know understanding of a agents and stuff like that. Now after the 30 secondond or so wait time these will receive their instructions and they'll

actually check the main thread and then they'll load in their websites. So this one up here spawned li I've never used that site before. This one's padmapper.com which is another one. You know these are all like websites and

resources I probably would not have looked at. And as a result I'm going to get more of like a search spread. I'm going to again a big chunk of the search space much faster than if I were to have done all this stuff manually. What's

cool is these can zoom directly into pages for me. These can click on links and stuff like that. They're obviously modifying filters and and whatnot autonomously so that they're not just getting a bunch of bogus results. And at

the end I get a high quality filtered list of apartments that are, you know, within my specifications. Okay, I just turned my camera off because I wanted some additional room on the bottom left hand side to really drill a few

important points home. The first is your context window. Now remember earlier how we talked about the claude.m MD, the Gemini MD, and then the agents.m MD.

Over here, we just have Claude, but I just want you to treat this as all uh three of them. That's not the only thing that gets injected, so to speak, in your context.

You have a variety of other things. Now, you have your system prompt up top. You then have the claw.md agents.mmd and whatever else. You have a file at least in cloud code called memory.md although there are analoges in other

coding platforms.

And then you also have skills and tools.

We've chatted a lot about MCP over the course the last hour and a half or so.

Right? Well MCP is a type of skill and tool. We also have the actual skills themselves. So remember the agent reviewer when we were doing sub agent verification loops. Well, that was an example of a skill. If you think to the

prompt contracts, those were examples of skills.

And the reason why I'm going into depth here is because each of these sections can consume a tremendous number of tokens. And you're not given an unlimited number of tokens to start with. Everything in life is finite,

including uh you know your claude or your Gemini context window. Now most models right now are somewhere between uh I don't know if it's like 4.6 we're probably talking 200K to 1 million. If we're talking Gemini, you know, we have

like 3.1 and there there a couple other ones obviously by the time you guys are watching this there'll probably be more.

And then you know you have uh GPT 5.4 4 and then codeex 5.3, but the 5.4 is coming out. You know, most models nowadays have somewhere in the realm of between 200k to 1 million. And to be clear, um, a token is not a word. A

token is about 0.7 words. So if you think about it in that vein, what this means is these 200k tokens sort of actually equate to somewhere between like 140,000 words to

about 700,000 words. Okay. Um but this context window obviously gets filled up the more that you talk with it. And unfortunately, one common and major problem in large language models, specifically the types that we're

dealing with in this course, are as time goes on and you talk to it more and more and more, what you find is the average quality goes down.

So quality as a factor or a byproduct of token count typically starts pretty high up here at maybe I don't know 100%.

And then the longer and longer and longer the number of tokens in your context the lower and lower and lower the quality gets. So maybe this is at 10k, maybe this is at 50k, maybe this over here is at 200k. And what that

means is let's just hypothetically say you're at your 199,000th token. Okay, that means that on a equivalent query that you might have previously scored 100% at at I don't know 5 or 10k tokens at

199,000 tokens you might only score 40% at. Now, these numbers I basically pulled out of my ass to be clear, but the point I'm trying to make is the longer the token count, basically the bigger the context length, the lower the

performance of the model. And so, understanding context windows and then learning a little bit of context management, ways to proactively manage all of these things, some of which you have control over and some of things

which you don't, is very important. It's also important, of course, because of billing. The more tokens that you use up, obviously the more money that you spend. And so, not only is it best from a quality perspective over here to try

and push to the left side of this graph as much as humanly possible, it's also very relevant from a financial perspective over here because obviously the more tokens that you use, the more money you spend. Case in point, just to

make this video, I've spent something around $500 or so in tokens. That's because I'm using a particular agent uh fast mode which bills me directly instead of just using a monthly plan.

But the point remains any sort of serious AI agent application will start spending and using a fair amount of your money. Okay, just before I move on, I want to talk a tiny bit about the differences between each of these in

length. If I open up an actual clawed instance here, open up one of these and then I go to terminal, which is the current best way to visualize this. Then if I just maximize this panel size, let's just make this as big as humanly

possible. Then I go /context, claude will show us all of the things currently consuming its tokens. I'm going to zoom in here to make it really, really clear what's going on.

This right over here is your context usage. And as you can see, they've illustrated this as sort of a series of squares where every square is, I don't know, let's see, 1 2 3 4 5 6 7 8 9 10.

Okay, every square is I think 2,000 tokens or so. And so what we're seeing is despite the fact that we have put no conversation tokens, so we haven't spent any tokens at all on conversation, we're still at 9,000 used.

You're probably wondering where the hell are these 9,000 coming from? Are they shadow billing me to try and uh rinse my wallet as much as humanly possible?

Well, a little bit. I mean this system prompt here, okay, which is partially composed by your agents, your Gemini or your clawmd and partially a few additional things is actually already consuming 4,900 tokens. So 2.5% of my

entire token count before I even send a message is being used by in this case probably the claw.md.

But in addition, you have other things like memory files which are consuming 2,000 tokens. Okay. And the way that they do that in cloud code is they use something called a memory MD which stores your preferences and some some

previous highle things. Then next up we have skills which are consuming 1,700 tokens. What are these skills? Well, you guys remember when we made a bunch over here? If I go to the top lefthand corner where it says docloud skills, you know,

every aenta coding platform has their own configuration for this stuff. But the way that it works in cloud code is, you know, you organize these workflows into these skills. Well, guess what?

These skills aren't free. In order for Claude to be able to use these skills, okay, this multi- aent orchestrator, it needs to store all these tokens somewhere and then give it to the model.

And that's what's going on over here.

Right now, the actual messages that we've used are only at eight tokens. And guess what? That's actually I think it's um this word here, context usage.

I'm not entirely sure, but I think context usage just because the way that it's broken or maybe context usage plus this term here /context, you know, is equal to 8 tokens, but know that, you know, that's that's it. That's it for

our whole token count. So, the other 158,000 of our 200,000 limit is currently free. And so, I mean, this is a quick and easy way obviously to visualize it inside of Cloud Code, but other platforms have their own

visualization mechanisms. Now, next up are these MCP tools. A way to look at these mcp chromedev tools_click.

What is that? Well, this is the tool that allows Chrome to click on parts of the page. Remember earlier when we were building that little nadn flow? Well, we were doing it by clicking on various parts of the page. How about drag?

Right? We can drag things. Get console message. These are all basically buttons in some colossal spaceship. Basically, we are in the cockpit with clawed code and we're telling it to do stuff for us.

We don't know what these buttons are. It does because it's, you know, the ship technician or the navigator, whatever.

And so, it's clicking these buttons left, right, and center for us to do various things. That's how you can conceptualize all these MCP tools and all these skills. And what I really like about this is it breaks everything down.

So here are our memory files, okay, which I talked about the memory MD, the cloudMD. You can see this is being contributed to in a variety of ways. We have a global cloud.mmd which is sort of like a very high level one with some

sparse instructions. We have the local cloudmd and we actually have the memory down here and then we have all the skills. You know what was really telling about that is despite the fact that in this diagram conversation history is

like the biggest chunk of it all. Notice that in reality conversation history for us at least at the beginning was nothing. you know, it was actually a tremendous number of tokens, about 10% of our entire context window dedicated

to just this little chunk. And that is a problem because if you're not careful, your cloud MD with all its rules are going to get really, really long. Your memory MD with all your preferences is going to get huge. Same thing with all

the skills and tools and stuff like that. And your conversation history when you actually do get to conversating with the model will be very, very, very small. you know, instead of starting, I don't know, somewhere in this region

here, you're actually because the context window of all of your BS is so big, you might actually like start in the effective area over here. And obviously, this is not what you want to begin an agent conversation at because

if you start here, then it's obviously only downhill from there. Now, this takes me to the logical question of, you know, hey, Nick, what happens when you run out of context? Because obviously that's going to happen. Well, when there

are 50,000 tokens, let's say out of 200,000, okay, no problem. You are having the full conversation history with the model, the model basically gets literally every message starting from message number 1 2 3 4 all the way down

to, I don't know, message number 25. And then what it does is it takes all of this context and then feeds it into its big neural network to generate message number 26, right? However, when we get to a certain length, right? I don't

know, let's say message 50. Obviously, there's no there's no tokens left anymore in in the context window. Maybe we're like 199. Well, not actually probably like 155k out of 200k. Well, what happens is all models now have some

sort of um what's called like autoco compact limit. I mean, basically all of them have adopted this convention where when the um number of tokens that you're using, let's say the limit is right over here. when the number of tokens that

you're using gets to this point, okay?

You know, it fills up then fills up, fills up, fills up and fills up. What happens is this triggers a mechanism called compaction where we take all of the information here,

which is I don't know maybe like 80% or so of the whole context, and then we compress it. I want you to imagine right now there's like a a big hydraulic press type thing over here and it's pushing all of this context down. It's squishing

it. Basically, what's going to occur is we're going to erase the vast majority of this and then, you know, instead of it consuming 80%, we're going to cram all that information into maybe I don't know 30 or 40% or so.

And so that is um called compaction. and it occurs on a relatively regular basis across the uh the model ecosystem. The issue with the compaction or you know compression or whatever the heck you want to call it the same idea is during

this summarization and like densification process we are going to drop outputs from tools. we are going to remove some information and context that might actually be useful to you now at you know message 50 for message 4 which

might actually like eliminate a mistake and so because of that you know you are going to lose some of the quality um the benefit is obviously you will significantly improve the information density and what do I mean by

information density I mean literally like if it's like um hello how are you doing I mean let's say somewhere in your context you have the term The sentence hello, how are you doing?

Well, hello is actually two tokens. How is one, are is one, you is one, doing is three along the question mark. So, in total, if you count all this stuff up, depending on the uh thing you're using to do the embedding, that's uh eight,

right? Well, you know, compaction is literally going to take this sentence and then it's going to compress it. So, it's going to say, "Hi, how are you?" So now instead of that's one token here, one token here, one token here, one

token here equals four, it will literally get all of the context that it can and then try and squish it so that the same meaning is available in fewer tokens and fewer words wherever possible. And then it'll just run this

naively across your entire um context.

And so this is going to occur every single time. Obviously, it's something that we want to avoid occurring if we have sensitive and important data, but you know, it does allow us to continue conversating with models. before we had

context compression and some form of autoco compaction. Um, basically we would just run out of tokens and we'd have to restart a totally new session.

So this just does sort of that intermediate step that most people were doing before where they would like like take all of that, you know, try and summarize it in some other model and then paste it back into uh into into

another one. Now that takes us to what most model practitioners are using nowadays, which is a variant of something that uh people call the iceberg technique. Now, in case you guys have never seen an iceberg before, I'm

Canadian, so we have them everywhere, including literally in the river across the street from my house. Not uh actual icebergs, but little ice floats. The way that they work is basically you have um a section that's visible above, which is

usually quite massive and quite intimidating. And then you're like, "Oh my god, that's a really big iceberg." And then what you don't realize is underneath the iceberg is actually like two or three times as big. And so above

the stuff that's like immediately visible or in our terms for the model accessible immediately is actually only a very small percentage of the total iceberg.

And so in the context of our model what we store above which is immediately accessible. It's just sort of the stuff that's like visible to the plain eye is we'll store our memory. We'll store our claude or our agents or our gemini.md.

We'll store our local memory as well.

There's different types. There's global local. We'll store all of the current task context. So everything that our tools are doing then maybe any active file content. Okay. And so all of this stuff here is like basically always

accessible to us. It's literally just in our prompt. But then what people are doing to reduce the total number of tokens that they require is they're abstracting away everything else. and then they're just making it accessible

to the model if it needs it. What I mean by that is instead of putting all of the files in your codebase in a prompt, what it does is it gives you a tool called read. And what read can do is read can at any time read a file. Okay, but

instead of putting the entire file in there for now, all it does is it just puts the titles. So if you say, "Hey, I want you to grab the um information on the iceberg technique." And then in your workspace, you have a file called

iceberg technique.md, it'll know. It doesn't actually have to read all of the files in your workspace.

It only has to read iceberg.mmd. Right?

Same thing with the full codebase. You have tools like gp and glob. And these tools are sort of analogous. Instead of reading a whole file, what this does, this allows you to hone in on a specific segment of text. You know, if this is my

entire code file, okay, and hypothetically, let's just say it's really big and you know, there's there's a lot of stuff, but the only thing that I actually care about is this little segment over here. Then why would I load

all of the I don't know 10k tokens? I don't need to. Okay. Realistically, what I can do as a smart model is I could use GP and Glob these tools to maybe hone in only on this segment over here, which is I don't know, let's just say 2K tokens.

And because it contains some of the text before and some of the text after, you know, this still usually gives us enough context to um tell the model what it needs in order to to finish its function. Now you also have web data via

web fetch. Web data is pretty cool. You can kind of think of it as the same thing. Obviously it doesn't have access to the whole internet, but it can make search queries, right? And so because it's able to use some general reasoning

when you say, "Hey, what's the iceberg technique?" First, it's going to start by looking for file contents called iceberg technique. It can't find any, maybe it'll quickly type fisceberg to look through the codebase. If it can't

find that, you know, maybe it'll look through some other things like uh memory files and the skills library. But if it can't find that, it'll say, "Okay, cool.

So, we don't have this in our in our context window right now, and we don't even have access to it within our space, but it's probably somewhere on the internet. So, I'm just going to Google iceberg technique. And then what it'll

do is it won't even take the entire thing. It'll just grab tople links, and then it'll look at the URL, you know, uh, and the URL is about, guess what?

Icebergs. I'm going off the map here, but hopefully you guys understand what I mean. Then, if there's three URLs, one of them is about icebergs, then instead of reading all of them, it's only going to read this one. And so it's sort of

like a successive narrowing of the lens until eventually it gets to, you know, what you want. And it doesn't load the entirety of all of the context, but it just has the opportunity to select all of this. You know, it starts here, it

goes here, goes here, goes here, goes here, goes here, and then goes here, and then finally it's at its goal. You can do the same thing in a variety of other ways. You can use bash, get history, and so on and so forth. But um essentially

what you want to do is instead of storing all of the information like the full code base, the file contents, the web data, all the git history, all the skills and everything like that, what you do is you just store the ability to

access it on demand. And then inside the context, okay, the tiny chunk that you do, I mean in this diagram it says 10% 90%, you know, I think in reality it's probably closer to 20 80 or maybe 30 70.

Um here's where you store stuff that's just like it it needs to be the same all the time. it always needs to be present.

There always needs to be some sort of patterns that are learned, some sort of active file context or uh contents or current task context. You can think of this as the difference between naive versus strategic context loading. Now,

way back in the day, and when I say way back in the day, I mean like 2023, good god, I'm getting old. You know, when you were working with an agent, you would dump in the whole codebase. You would honestly just copy and paste everything

and just hope to God that it that it knew what it was doing. Obviously, because this was extraordinarily infeasible, there were so many tokens in the context, tons of it was lost and you routinely ran out of context limits.

Well, nowadays what we've done is we basically built in a whole tool stack where instead of all of the file, you just read selectively and only the relevant functions. You know, you have a clawmd which is basically a compression

a compression function which just stores your preferences. skills instead of all being read, you know, we only read a specific segment of them. This is technically called the YAML front matter, which is just a tiny little

section at the beginning of the skill.

You can actually see this if we go back to the skill.md and I make this visible, right? Only this section up here is actually, you know, you can actually see this up here. Um, the YAML front matter is this segment. Only this segment is

actually loaded into context until you ask for, you know, more information about create proposal. And that's just because this little space invader sees you. It has the ability to call a create proposal skill, but it doesn't need to

know all the rest of this because what's realistically going to happen? Well, 90% of the time you won't even ask. There's so many other skills it'll probably be using. We're also now doing things like summarizing tool results. So instead of

storing the entire thing in your context, you know, we just store like a very short summary of basically the input output. So way back in the day, I used to think that all of an agent was really just its intelligence. So it was

just the core model, right? Which in this case would be Opus 4.6.

But what I've come to quickly realize is although models themselves are quite intelligent, it's really the architecture that we've wrapped around it. I want you to pretend this little space invader, it's kind of now in, I

don't know, a house of some kind. And the house has a little chimney with a fireplace. It has a little place where it could, I don't know, roast a nice turkey. You know, has a nice bed that it can go to sleep in every night. you

know, this agent by itself probably wouldn't last super long out there on the savannah. But because we've built all this infrastructure around it because we built roads for it, we built ways for it to communicate and stuff

like that. You know, it's capable of actually doing a lot of very economically valuable work for us. And so, just like human beings, uh, way back in the day had to conceptualize the idea of, I don't know, like a like a spear or

something to hunt, um, um, saber-tooth tigers on the planes, you know. So too do these agents use tools effectively to solve problems in their environment and ultimately get us the users what we want. Now obviously there's context

window management like we just talked about and that's for optimizing the usage of a specific model okay in the choice of a model. But there's also the ability to choose different models for different purposes. Now, throughout most

of the course so far, what I've done is I've just used mostly naive like Opus 4.6 agents in order to spawn other Opus 4.6 sub agents. And that was mostly for capability sake because at least in my case, cost is not a a concern. And I

really do want to eek out the marginal quality um benefits wherever possible.

But there are a lot of cases specifically like enterprise and and big infrastructure ones where, you know, people are actually comfortable making a miter tradeoff for quality. I'm going to draw another one of my famous graphs.

Um, people are comfortable making, you know, a trade-off in terms of, you know, cost and then quality. Now, in a lot of disciplines out there, biology, physics, chemistry, and stuff, there's this this idea of like this inverted U curve, and

you can call it whatever the heck you want. Um, I think the actual name is the Yorky's Dodson curve.

And what this is is this is basically like the the optimal point that combines two different factors. And so in our case, if we're optimizing for both cost and quality, okay, simultaneously, not just cost, not just

quality, you can imagine that the optimal place to choose on this graph is probably going to be something like over here. It's going to be it's going to be somewhere around here. If you wanted to minimize cost exactly, we'd probably go

like way over here. But obviously, we care about quality as well. So, we're going to push up a little bit, right? We don't want this point because one, it costs a lot. And then boom, two, the quality is pretty low because despite

the fact that quality is really really high, um you know, cost is like many many times higher than it was over here.

And so this is sort of like our our optimal point. And you know, a lot of large enterprises, since we're dealing with hundreds of millions of dollars here, um, are actually comfortable making a little trade-off where, you

know, if this quality is 85% and then this one here is, I don't know, 95%, they're okay taking like a like a 10% hit here, if it means that they also reduce their costs by, I don't know, 40%. Or something like that. And this is

really where all this stuff comes in.

Okay? So, I don't mean to talk your ear off here. It's not super important, but uh basically uh what a lot of people have taken to doing now is doing a 60/30 10 rule where they'll use some top level agent router which is sort of like the

orchestrator in our multi- aent Chrome window example. And what that agent writer does is it calls dumber models and then it assigns different strengths to tasks. So that you know if you're giving it a really simple task and you

say hey you know I just want you to classify this into one of three categories and it's really dumb. It's like you know red, blue or green, angry, serene or or healthy or whatever the heck. um you don't have to use like

Opus, which is like space age intelligence and costs you a ton more in token cost in order to get that done.

Instead, you know, you can get all the way down to like a haik coup or maybe a Gemini flash model or something like that. Likewise, if you have some other task here and maybe that task requires a lot of um I don't know, research or

something and you say, "Hey, I want you to go and compile 200 million tokens worth of stuff and then um give it to me in a big report." Well, you know, you probably don't want the dumbest model to do that for you, but you also don't need

the most expensive model. So maybe you'll use something like a sonnet or like a a lower level GPT model which might cost 2 or3 million uh $2 or $3 per million tokens instead. And so you know this allocation where you have 60 3010

if you think about it like sort of a pie chart. Um what you do is you designate you know the vast majority of your token usage to stuff that is in that first category which is kind of you know dumber. And then what you do is you do

the other 30% or so in sort of that mid tier and then your really really really smart models, you know, they do the highest level tasks.

And basically what'll happen for the most part is this would be, you know, your Opus 4.6 or your Gemini 3.1 or your GPT 5.4. It would be responsible for routing decisions and obviously you want the smartest model

possible for that. But all of the heavy lifting, all the contacts and stuff like that is um through sub agents that are spawned either Haiku, Sonnet or uh you know, I don't know if if you wanted to do a really smart call, then you'd

obviously spawn an Opus sub agent like me as well. And if you do all this, you could significantly reduce the cost. I mean, like just just think about it mathematically. If previously you were doing 100 million tokens times, you

know, $5 per 1 million tokens, what's the cost there? Well, that's obviously going to cost $500. And so that's like your opus only, right? But if you did 10 million * $5 plus 30 million * $3 plus 60 million * $1.

Well, what's the total cost going to be now? Well, it's going to be 60 + 90 + 50 or in total 200. And so you know 200 expressed as a fraction of 500 is 40% of our total cost and we will have just saved you know 60% with probably

minimal impacts on quality because the things that we're now spawning you know dumber agents um to do are things that to be honest the quality was already okay a few generations ago back at the haikus and the sonnetss. So just to give

you an example from something that I do pretty often, okay, which is going to be some form of lead scraping. What you can do is you can actually traverse a very large portion of the internet using a a relatively dumb model. These haiku

models, what these do is these um scrape a vast majority a vast amount of internet data. Okay, all of the code of uh I don't know, let's say 10,000 websites or something. And then in doing so, they just like that little

magnifying glass, use some sort of GP or extraction prompt to look for things that are formatted like email addresses.

So if you have like something and then it's an at and then it's a, you know, the term gmail.com, odds are this is a real email address, right? And you store that to a database. And because this is just such like a mass data application,

you use haik coup that drives the cost really, really low. Well, then maybe um the actual enrichment point, you know, takes significantly more intelligence.

And so maybe here we'll use sonnet and it'll cost us uh 0.008 cents per lead.

08 per lead. The actual outreach part is mostly templated. So we'll use sonnet for that as well. And then maybe at the end we just have a quality review step to make sure things aren't absolutely nuts. Well, when you do it this way, um

you know, the math ends up being uh 08 plus 05. So that's 013 plus 01.014 plus 015 is 029. And then if you were to go 100% opus, then it would be I don't know uh about 12 cents or so per lead. And so on a list of let's just say a thousand,

which is approximately how much I'm sending a day right now. I'm much farther down than my maximum. But if we multiply all these together, we move that one to three decimal points over to the left. Then that um ultimately would

be $15 a day or you know $450 a month. Well, instead I'm doing that for literally one quarter of this or something like, you know, $120 a month instead. Obviously, I'd much rather the latter. And if my

quality is only going down a few percentage points because of that Yorky's Dodson curve, you know, I'm okay being over here instead of over here because this gap to me is fine on tasks that aren't super high and high quality.

Then, uh, this is a very, very efficient stack. And you know, the bigger and bigger my company gets, whoever I'm working with, the more the cost per lead is going to be important versus the actual quality. I've included just a

little LLM API pricing cheat sheet. I don't expect this to be super relevant or useful to you guys. There are a lot more models for OpenAI and Google, but I am actually using um not this model series anymore, but this one here for

some queries. I'm also using the Flash model series for some queries as well.

And then what's really cool is a lot of them offer what's called a batch API now where you can submit a bulk number of requests over um simultaneously and then if you're comfortable waiting like a day or so what the companies do is they

batch it and then they serve your requests during periods in which they have very low inference or low competition. So maybe in the middle of the night or something like that. And in doing so they actually get to load

balance. Like if you think about it, like if this is like a day and then this is their load like on their servers and their neural networks and stuff, you know, it probably peaks somewhere around like noon and there's probably like a

couple things and then it's like low during the during the day, right? I don't know, this is like 4:00 a.m. What they'll do is they'll actually take all of your queries, batch them, and then they'll just like run them over here

when there's very little competition.

And then later when you know the things go up and stuff like that again, that's okay. And in doing so, what they want to do is they want to shift some of the the really top end of all of these users um to the low end to basically fill this so

that they have a lot more like dependable load instead of these like uh jagged peaks and whatnot. But anyway, don't worry too much about that. I just wanted to cover um some LLM pricing principles as well, so you guys know not

only how to manage your contacts better, but also how to um save, especially when you get into more sophisticated multi- aent setups like I've been showing you.

And that's it. Thank you guys very much for watching this video end to end. If you guys have made it all the way to this point in the course, you're part of like the 2 or 3% that actually do. Um, I'd really appreciate a big solid if you

could do me a favor and subscribe to the channel. Something like 70% of you aren't, which significantly hurts my reach and uh, despite me hating asking for it, it does help the channel grow.

So, if I've given you guys any value whatsoever, please do that. You can also send me over a comment down below asking any question about any point in the video. Um, I'm much more engaged than the average YouTuber. So, the

probability that I will reply is pretty pretty far up there, I would say, statistically. Um, if you guys have any, you know, suggestions for future videos or future courses, please drop them down below as well. And above all else, keep

learning and growing with AI agents.

This is by far the biggest and most impactful of economic changes that I think any of us will see in our lifetime. It's a blessed time to be alive in general. You might as well not waste it. Make the most out of it. All

right. Um, thank you very much. Feel free to use the chapter headings to revisit any section in the course. And uh looking forward to seeing all y'all in the next one.
