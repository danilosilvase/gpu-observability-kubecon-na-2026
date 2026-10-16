# Slide by slide: intention, what the audience gets, caveats

For Henrique. Why each slide is in the talk (from the grill session, decisions in TALK-DECISIONS.md), what the room should leave with, and what to watch out for on stage.

| # | Slide | Time, who, clicks | Intention (why it is here) | The audience gets | Caveats on stage | Decision |
|---|---|---|---|---|---|---|
| 2 | Title | 0:00 to 0:30, Henrique | Set the deal: one question, a live answer, then questions | A reason to stay: there is a payoff, live | Keep it to 30 s | S8 |
| 3 | Which one is in trouble? | 0:30 to 2:00, Henrique, 3 | Cold open. Make the room commit to an answer, so the demo is a reveal, not a lecture | A stake in the answer. Most will vote 8%; the right answer is "both" | Do NOT reveal. Say "a test cluster we built for this talk". If asked: model is opt-125m (small on purpose) | S1, 3, 5 |
| 4 | A setting, not a signal | 2:00 to 3:30, Henrique, 4 | Break trust in the chart people page on | GPU memory is a config value: flat whether busy or idle | Don't say CPU or memory metrics are useless, only that they can't see the queue. Request bars are illustrative. 0.92 default is checked in the vLLM code | S2 |
| 5 | What runs out first | 3:30 to 6:00, Henrique, 5 | Bridge from known to new: a mental model (connection pool) so KV cache % makes sense before the demo | KV cache = room for requests in flight. Full means waiting. vLLM prints the number in its log | Analogy breaks on preemption (vLLM can evict work, a pool can't). Do not name a pod: it spoils the vote. Jimmy Song credit is in the footer | S3, 9 |
| 6 | Live demo | 6:00 to 15:00, Danilo | Prove it live: answer the vote with evidence, following one pod from GPU to log to trace to verdict | Sees the same pod across three signals; watches Pod A fill about 68 s after load starts | Script runs 10 min for a 9 min slot: trim screen 3. Rig dead: clean video. Video dead: hidden slide 7. One laptop, Cmd+Tab in and out | 7, 10 to 12, S6, S7 |
| 8 | What broke | 15:00 to 17:30, Henrique, 3 | Credibility through honesty, and the abstract promised cardinality | Three traps for their own tests: repeated prompts, pod-name cardinality, unfair traffic | If the slide starts after 16:30, skip "An unfair test". 14 and 56 are for our 7 counters | S4 |
| 9 | Who voted both? | 17:30 to 18:00, Henrique, 3 | Close the loop opened on slide 3 and land the takeaway word for word | Both settings were wrong, in opposite ways. "GPU memory can't tell you an inference server is in trouble. Read the server's own signal." | Numbers are for opt-125m on one A10G; they don't predict anyone's latency. "Too big" is waste, not slowness | 1, S5, S10 |
| 10 | Three lines of config | 18:00 to 18:45, Henrique, 4 | Deliver the abstract's "deployable configs" promise and show the trick is the join | One line per tool, and the pod name as the key that lines them up | Expect "vLLM already has /metrics": yes, hidden slide 13. Pod name is also the cardinality cost from slide 8 | 2, S10 |
| 11 | Size it from peak KV cache | 18:45 to 19:30, Henrique, 4 | Give them something to do on Monday | A method and 3 steps: measure peak, change the flag, measure again. Repo QR | Say out loud that 40% and 90% are our rule of thumb, not vLLM's. Use the method, not our numbers | 4, S11 |
| 12 | Questions | 19:30 to 25:00, both | Q&A with the feedback QR up the whole time | A way to rate the session and the repo | Replace "[original author]" before the talk. Hidden answers: type the number and Enter | S5 |

## Hidden slides (Q&A only, type the number and press Enter)

| # | Question it answers | Who | Intention |
|---|---|---|---|
| 7 | (demo backup) What screen 4 showed | Danilo | Only if the rig AND the video fail |
| 13 | Why parse the log if vLLM has /metrics? | Danilo | Admit it upfront: scrape /metrics if you can; the log path needs no new target and works for servers that only log it |
| 14 | Why not set 0.90 everywhere? | Henrique | Fine for one pod per GPU; the cost is reserved memory on shared GPUs |
| 15 | What about GPU utilisation? | Danilo | GPU_UTIL means "a kernel ran"; profiling fields say more; none sees the queue |
| 16 | How much does the pod name cost? | Danilo | 14 to 56 series after 3 rollouts; keep the pod name, drop what churns |
