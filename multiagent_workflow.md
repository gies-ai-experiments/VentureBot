# VentureBots: AI-Powered Entrepreneurship Coaching Workflow

VentureBots guides students through the entrepreneurship journey using specialized AI coaches developed by VentureBot at Gies College of Business.

```mermaid
%%{init: {'flowchart': {'useHtmlLabels': true}}}%%
flowchart TD
    Student([Student]) -->|Problem Statement| Node1
    
    Node1[1. @Orchestrator<br><br>Mission: Parse student inputs, choose coaching specialists,<br>merge guidance, handle safety & rate-limits<br><br>Input: Learning goals from student<br><br>Output: Directs to relevant coaching agent] -->|Store/Retrieve Data| Memory[(Learning Progress / Vector Store)]
    Memory -->|Cached Results| Node1
    
    subgraph Idea-Generation-Loop
        Node1 -->|Generate Ideas Request| Node2[2. @Idea-Coach<br><br>Mission: Guide students through structured brainstorming:<br>market gaps, problem framing, How-Might-We coaching<br><br>Input: Problem Statement<br><br>Output: Coach student to generate top 5 ideas]
        Node2 -->|Prompt| LLM1[LLM]
        LLM1 -->|Raw Output| Node2
        Node2 -->|5 Ideas| Node1
    end
    
    subgraph Validation-Loop
        Node1 -->|Validate Ideas Request| Node3[3. @Validation-Mentor<br><br>Mission: Coach students through TAM/SAM analysis, competitor scans,<br>persona sketches, lean-canvas methodology<br><br>Input: 5 ideas from @Idea-Coach<br><br>Output: Guide students to score impact, feasibility,<br>innovation + research similar solutions]
        Node3 -->|Scoring Criteria| LLM2[LLM]
        Node3 -->|Keywords| GoogleAds[Google Ads Metrics]
        GoogleAds -->|Market Data| Node3
        LLM2 -->|Scores| Node3
        Node3 -->|5 Scored Ideas| Node1
    end
    
    Node1 -->|Present 5 Scored Ideas| Student
    Student -->|Select Final Idea| Node1
    
    Node1 -->|Chosen Idea| Node4[4. @Product-Manager<br><br>Mission: Coach students through PRD development, user story writing,<br>acceptance criteria mapping<br><br>Input: Final idea from @Orchestrator<br><br>Output: Guide students to create PRD, user stories, and feature list]
    
    Node4 -->|Product Details| Node5[5. @Prompt-Engineer<br><br>Mission: Coach students to optimize development prompts<br>for Lovable.dev/Bolt.new and similar tools<br><br>Input: Info from @Product-Manager<br><br>Output: Guide students to create 5 step-by-step optimized prompts]
    
    Node4 -->|Product Details| Node6[6. @Pitch-Coach<br><br>Mission: Coach students through slide deck creation,<br>speaker notes development, elevator pitch crafting<br><br>Input: Final product details from @Product-Manager<br><br>Output: Guide students to create 90-sec elevator pitch]
    
    Node5 -->|Optimized Prompts| Node1
    Node6 -->|Elevator Pitch| Node1
    
    Node1 -->|Final Learning Deliverables| Student
```