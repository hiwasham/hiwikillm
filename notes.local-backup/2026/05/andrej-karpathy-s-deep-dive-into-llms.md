---
title: "Andrej Karpathy's Deep Dive Into LLMs"
source: "https://www.youtube.com/watch?v=7xTGNNLPyMI"
kind: "youtube"
captured_at: "2026-05-25T14:41:05.698944+00:00"
tags:
  - llms
  - transformer
  - pretraining
  - post-training
  - tokenization
  - reinforcement-learning
  - ai-tools
---

# Andrej Karpathy's Deep Dive Into LLMs

> A general-audience technical walkthrough of how ChatGPT-like LLMs are trained, post-trained, sampled, and practically used.

## TL;DR

- LLMs begin as base models trained to predict the next token over massive internet-text datasets; the result is an "internet document simulator," not yet an assistant.
- Pretraining data pipelines start from sources like [[Common Crawl]], then apply URL filtering, text extraction, language filtering, deduplication, and PII removal; [[FineWeb]] is a representative public example at about 44 TB and 15 trillion tokens.
- Tokenization converts text into one-dimensional token sequences; GPT-4's tokenizer uses 100,277 possible symbols, and tokenization creates many model quirks around spelling, casing, spacing, and arithmetic.
- A Transformer is a stateless mathematical function with billions of parameters; training adjusts those parameters so predicted next-token probabilities match the training corpus.
- Inference samples one token at a time from probability distributions, feeding generated tokens back into the model; outputs are stochastic "remixes" rather than deterministic database lookups.
- Post-training turns a base model into an assistant by continuing training on conversation datasets, usually created or edited by humans and increasingly synthesized with LLM help.
- Later sections cover hallucinations, tool use, working memory, self-knowledge, "models need tokens to think," jagged intelligence, supervised fine-tuning, reinforcement learning, [[DeepSeek-R1]], [[AlphaGo]], RLHF, model tracking, and local/cloud inference options.

## Key claims & findings

- Pretraining starts by "download and process the internet," aiming for "large diversity of high quality documents" at huge scale.
- [[FineWeb]] is used as the main public example of a production-like pretraining dataset:
  - about 44 TB of disk space;
  - about 15 trillion tokens;
  - focused heavily on English by keeping pages with more than 65% English.
- [[Common Crawl]] has been crawling the internet since 2007; as of 2024 it had indexed 2.7 billion web pages.
- Typical pretraining-data filtering stages include:
  - URL/domain blocklists for malware, spam, marketing, racist, and adult sites;
  - HTML-to-text extraction that removes markup, navigation, CSS, and boilerplate;
  - language classification and filtering;
  - deduplication;
  - PII removal, including addresses and Social Security numbers.
- Neural networks expect a one-dimensional sequence of symbols from a finite vocabulary; raw UTF-8 bits are too long, so tokenization trades a larger vocabulary for shorter sequences.
- Byte Pair Encoding groups frequent adjacent byte/symbol pairs into new symbols, iteratively shrinking sequence length while increasing vocabulary size.
- GPT-4's tokenizer has 100,277 possible symbols; "hello world" can tokenize differently depending on spaces, casing, and punctuation.
- The model input is a context window of tokens, with a maximum context length chosen for compute reasons; examples given include 4,000, 8,000, 16,000, hundreds of thousands, and possibly around one million tokens for modern systems.
- Training objective: given context tokens, output one probability for each token in the vocabulary as the next-token prediction; adjust parameters to increase probability of the true next token and lower the others.
- The model starts randomly initialized; early predictions are random, and training iteratively tunes parameters so outputs match statistical patterns in the dataset.
- A Transformer is described as a "giant mathematical expression" mixing inputs and parameters through operations like multiplication, addition, exponentiation, division, layer norms, matrix multiplications, softmaxes, attention blocks, and MLP blocks.
- Transformer activations can be loosely analogized to synthetic neuron firing rates, but Karpathy warns that biological neurons are much more complex and have dynamical memory; the Transformer forward pass itself is stateless.
- Inference is autoregressive: start with prefix tokens, predict a distribution for the next token, sample a token, append it, and repeat.
- Because inference samples from probabilities, the same prompt can produce different continuations; generated text is statistically similar to training data but not usually identical.
- ChatGPT inference does not update the model's weights; the model was trained earlier, its parameters are fixed, and interaction is token-sequence completion.
- [[GPT-2]] is presented as the first recognizably modern GPT stack:
  - released by [[OpenAI]] in 2019;
  - Transformer architecture;
  - 1.5-1.6 billion parameters;
  - 1,024-token maximum context length;
  - trained on roughly 100 billion tokens.
- GPT-2 training cost was estimated around $40,000 in 2019; Karpathy's [[llm.c]] reproduction cost about one day and $600, with a claim it could likely be reduced to about $100 today.
- Cost reductions came from better datasets, faster hardware, and much better software for extracting performance from hardware.
- In a GPT-2 reproduction run:
  - each optimization line/update improves prediction on about 1 million tokens;
  - each update takes about 7 seconds;
  - the example uses 32,000 optimization steps;
  - 32,000 steps x 1 million tokens is about 33 billion tokens processed;
  - the loss should decrease during training, and lower loss is better.
- The example compute node is an 8x NVIDIA H100 machine rented in the cloud; Lambda pricing cited is $3 per GPU per hour for 8x H100 on-demand.
- GPUs are central because neural-network training contains highly parallel matrix multiplications.
- NVIDIA's market value is cited as $3.4 trillion, driven by demand for GPUs for training LLMs.
- Elon Musk's reported 100,000-GPU data center is used as an example of scale: many GPUs collaborating to predict next tokens faster and train larger models.
- A model release requires two things:
  - code implementing the neural-network forward pass, often a few hundred lines;
  - the trained parameters, e.g. a list of 1.5 billion numbers for GPT-2.
- [[Llama 3.1]] is used as a modern open model example:
  - trained by [[Meta]];
  - biggest released base model: 405 billion parameters;
  - trained on 15 trillion tokens;
  - released as both base and instruct variants.
- A base model is not an assistant; it is a token simulator that "dreams internet pages."
- Base-model prompting can still elicit behavior through prompt design:
  - "Here's my top 10 list..." can elicit factual list continuations;
  - few-shot prompts can perform translation through in-context learning;
  - a fabricated web-page-like conversation can make the base model imitate an assistant.
- Model knowledge is stored in parameters as vague, probabilistic recollection, not as explicit records; common internet facts are more likely to be remembered correctly than rare facts.
- Base models can regurgitate training data exactly, especially high-quality repeated sources like Wikipedia; Karpathy suggests a Wikipedia zebra article may have been seen around 10 times.
- [[Llama 3.1]]'s pretraining data cutoff is cited as the end of 2023; when prompted about the 2024 election, the base model invents plausible continuations, e.g. Trump with Mike Pence against Hillary Clinton and Tim Kaine, or Trump with Ron DeSantis against Joe Biden and Kamala Harris.
- Hallucination is framed as the model taking its best probabilistic guess when continuing a token sequence, especially beyond its training data or knowledge.
- Post-training replaces internet-document data with conversation data and continues training the same model with the same next-token objective.
- Pretraining may take roughly three months on many thousands of computers; post-training may take roughly three hours because conversation datasets are much smaller.
- Conversation data "programs" the assistant by example: human/assistant turns encode how the model should respond, refuse, be helpful, be truthful, and be harmless.
- Conversations are serialized into one-dimensional token sequences with special tokens, e.g. GPT-4o-style markers such as `im_start`, `im_sep`, and `im_end`; these protocol details vary by model and remain somewhat "wild west."
- The example "What is 2 plus 2? / 2 plus 2 is 4" conversation becomes 49 tokens in the tokenizer demonstration.
- During assistant inference, the server constructs the serialized conversation context ending with an assistant-start marker, then samples assistant-response tokens.
- [[InstructGPT]] is presented as the first major OpenAI paper explaining how to fine-tune language models on conversations.
- InstructGPT used human contractors from [[Upwork]] and [[Scale AI]] to create prompts and ideal assistant responses.
- InstructGPT labelers were instructed at a high level to be helpful, truthful, and harmless; real labeling instructions can be hundreds of pages.
- [[Open Assistant]] is shown as an open-source analogue of human-created conversation data.
- [[UltraChat]] is cited as a more modern supervised fine-tuning dataset with millions of conversations, largely synthetic with some possible human involvement.
- Modern post-training data is increasingly generated, assisted, or edited by LLMs rather than written from scratch by humans.
- Chapter topics beyond the transcript include:
  - hallucinations, tool use, knowledge memory, and working memory;
  - knowledge of self;
  - why models need tokens to think;
  - tokenization revisited and spelling difficulty;
  - jagged intelligence;
  - supervised fine-tuning to reinforcement learning;
  - [[DeepSeek-R1]];
  - [[AlphaGo]] and Move 37;
  - reinforcement learning from human feedback;
  - tracking LLMs through rankings/newsletters;
  - finding and running LLMs through cloud playgrounds or local tools.

## Entities & links

- [[Andrej Karpathy]]
- [[ChatGPT]]
- [[OpenAI]]
- [[Eureka Labs]]
- [[Large Language Model]]
- [[Transformer]]
- [[Common Crawl]]
- [[FineWeb]]
- [[Hugging Face]]
- [[Byte Pair Encoding]]
- [[Tiktokenizer]]
- [[GPT-4]]
- [[GPT-4o]]
- [[GPT-2]]
- [[llm.c]]
- [[Llama 3.1]]
- [[Meta]]
- [[Hyperbolic]]
- [[InstructGPT]]
- [[Open Assistant]]
- [[UltraChat]]
- [[Upwork]]
- [[Scale AI]]
- [[NVIDIA H100]]
- [[Lambda]]
- [[DeepSeek-R1]]
- [[AlphaGo]]
- [[Reinforcement Learning from Human Feedback]]
- [[LM Arena]]
- [[AI News Newsletter]]
- [[LMStudio]]
- [[TogetherAI Playground]]
- [[HuggingFace inference playground]]
- [[Excalidraw]]

## Open questions

- How much exact memorization remains in modern frontier assistants after deduplication, post-training, and safety filtering?
- What are the precise dataset mixtures and filtering policies used by closed models such as ChatGPT, Claude, and Gemini?
- How do different tokenizers affect spelling, arithmetic, multilingual performance, and reliability in practice?
- What fraction of modern supervised fine-tuning data is human-written, human-edited, fully synthetic, or model-ranked?
- Which post-training stages contribute most to assistant usefulness: supervised fine-tuning, reinforcement learning, RLHF, tool-use data, or system-prompt scaffolding?
- How should users distinguish model knowledge, working memory, external tool results, and hallucinated continuation during real tasks?
- What evaluation methods best capture "jagged intelligence," where a model is strong on some nearby tasks but surprisingly weak on others?
- How do DeepSeek-R1-style reinforcement-learning recipes change the cost and accessibility of high-quality reasoning models?
- What are the practical limits of local inference with tools like LMStudio compared with hosted frontier models?

## Source

https://www.youtube.com/watch?v=7xTGNNLPyMI