"""Beginner-friendly explanations and extra interview Q&A: statistics, data science, ML/AI, analytics."""

NOTES = {
    "Descriptive Statistics & Distributions": {
        "simple": [
            ("Mean", "The average: add everything up and divide by the count. One huge value (a billionaire in the room) can drag it a lot."),
            ("Median", "The middle value when sorted. It isn't pulled by extremes, so it's better for salaries and house prices."),
            ("Standard deviation", "How spread out the numbers are. Small means values sit close to the average; large means they're all over the place."),
            ("Normal distribution", "The bell curve: most values near the middle, fewer at the edges. About 68% fall within one standard deviation of the mean."),
            ("Outliers", "Unusually high or low values. Investigate them before removing; they might be errors or the most interesting data."),
        ],
        "qa": [
            ("When is the mean misleading?", "With skewed data or outliers, such as incomes, where a few very large values make the 'average' unrepresentative. Use the median."),
            ("What is the IQR?", "The interquartile range: the spread of the middle 50% of data (Q3 − Q1). Values beyond 1.5 × IQR from the quartiles are often flagged as outliers."),
            ("What's a skewed distribution?", "One with a long tail on one side. Right-skewed (like income) has a long tail of high values, so mean > median."),
        ],
    },
    "Inferential Statistics & Hypothesis Testing": {
        "simple": [
            ("Sample vs population", "We usually can't measure everyone, so we study a sample and use statistics to make careful guesses about the whole population."),
            ("Null hypothesis", "The 'nothing special is happening' assumption, such as 'the new button doesn't change clicks'. We test whether data gives strong evidence against it."),
            ("p-value", "If nothing special were happening, how likely is a result at least this extreme? Small p (below 0.05) means 'unlikely to be chance'."),
            ("Confidence interval", "A range likely to contain the true value, such as 'conversion lift between 1% and 4%'. More data gives a narrower range."),
            ("Type I and II errors", "Type I: a false alarm (saying there's an effect when there isn't). Type II: a miss (failing to spot a real effect)."),
        ],
        "qa": [
            ("Does p = 0.03 mean a 97% chance the result is real?", "No. It means that if there were no effect, data this extreme would appear 3% of the time. It isn't the probability the hypothesis is true."),
            ("What is statistical power?", "The chance of detecting an effect if it really exists. More data and bigger effects increase power; 80% is a common target."),
            ("When would you use a t-test vs a chi-square test?", "A t-test compares averages of numeric data between two groups; chi-square tests relationships between categories, like counts in a table."),
        ],
    },
    "Probability for Interviews": {
        "simple": [
            ("Probability", "How likely something is, from 0 (impossible) to 1 (certain). A fair coin landing heads is 0.5."),
            ("Independent events", "One doesn't affect the other, like two coin flips. Multiply probabilities: two heads = 0.5 × 0.5 = 0.25."),
            ("Conditional probability", "Probability given that something already happened, such as the chance it's raining given the ground is wet."),
            ("Bayes' theorem", "A way to update beliefs with new evidence. It explains why a positive test for a rare disease can still mostly be a false alarm."),
            ("Expected value", "The average outcome if you repeated something many times. For a fair die it's 3.5."),
        ],
        "qa": [
            ("What's the probability of at least one six in four rolls?", "1 − (5/6)^4 ≈ 0.52. It's easier to compute 'no sixes' and subtract from 1."),
            ("Explain the birthday paradox.", "In a group of 23 people there's about a 50% chance two share a birthday, because there are many possible pairs (253)."),
            ("Why do rare-disease tests give many false positives?", "If the disease is rare, even a small false-positive rate applied to many healthy people outnumbers the true positives. That's Bayes' theorem."),
        ],
    },
    "Data Cleaning & Feature Engineering": {
        "simple": [
            ("Missing values", "Decide why they're missing, then drop the row or column, fill with the median or mode, or add a 'was missing' flag."),
            ("Categorical data", "Models need numbers. One-hot encoding turns 'colour = red/blue' into separate 0/1 columns."),
            ("Scaling", "Put features on similar scales (like 0–1) so distance-based models aren't dominated by big-number columns."),
            ("Feature engineering", "Create helpful new columns from existing ones, like 'days since last purchase' or 'price per square foot'."),
            ("Data leakage", "Accidentally giving the model information it won't have when making real predictions. It makes models look great in testing and fail in reality."),
        ],
        "qa": [
            ("Why fit preprocessing only on training data?", "If you calculate means or encodings using test data too, information leaks into training and your test score becomes too optimistic."),
            ("How do you handle a column with thousands of categories?", "Group rare categories as 'other', or use frequency or target encoding, or embeddings for very large sets."),
            ("What's the difference between normalisation and standardisation?", "Normalisation rescales to a range like 0–1; standardisation shifts to mean 0 and standard deviation 1."),
        ],
    },
    "Exploratory Data Analysis & Visualisation": {
        "simple": [
            ("First look", "Check the size, column types, missing values and duplicates before anything else."),
            ("Distributions", "Histograms and box plots show how each column's values are spread and reveal outliers."),
            ("Relationships", "Scatter plots and correlation tables show how columns move together."),
            ("Target balance", "For classification, check how many examples each class has. Rare classes need special handling."),
            ("Tell a story", "Each chart should answer one question, with clear labels and a one-line takeaway."),
        ],
        "qa": [
            ("What does correlation tell you, and what doesn't it?", "How strongly two variables move together, from −1 to 1. It doesn't prove one causes the other, and it misses non-linear patterns."),
            ("Which plot would you use to compare groups?", "Box plots or bar charts with error bars for numeric values by category; grouped bar charts for counts."),
            ("How do you spot data quality issues during EDA?", "Look for impossible values (negative ages), sudden jumps over time, duplicate IDs, and categories with typos."),
        ],
    },
    "Supervised Learning Models": {
        "simple": [
            ("Supervised learning", "Learn from examples that include the answer, like emails labelled spam or not spam, then predict answers for new examples."),
            ("Linear regression", "Fits a straight line to predict a number, such as house price from size."),
            ("Logistic regression", "Predicts the probability of a yes/no outcome. Despite the name, it's used for classification."),
            ("Decision trees", "A flowchart of yes/no questions that ends in a prediction. Easy to understand, but a single tree overfits."),
            ("Ensembles", "Combine many trees: random forests average them (more stable), gradient boosting builds them one by one, each fixing earlier mistakes (often most accurate)."),
        ],
        "qa": [
            ("How do you choose between models?", "Start with a simple baseline, compare models using cross-validation on the right metric, and consider speed and interpretability."),
            ("What is regularisation?", "A penalty on overly complex models that discourages large weights and reduces overfitting. L1 can drop useless features; L2 shrinks all weights."),
            ("Why might a model perform well on training data but badly on new data?", "It's overfitting: it memorised noise instead of patterns. Use simpler models, more data, regularisation or cross-validation."),
        ],
    },
    "Model Evaluation & Validation": {
        "simple": [
            ("Train, validation and test", "Learn on training data, tune on validation data, and report the final score on test data the model has never seen."),
            ("Cross-validation", "Split data into k parts, train k times using a different part for testing each time, and average the scores for a more reliable estimate."),
            ("Precision", "Of everything the model flagged as positive, how much was right? Important when false alarms are costly."),
            ("Recall", "Of all the real positives, how many did the model catch? Important when missing one is costly, like disease detection."),
            ("Confusion matrix", "A 2×2 table of true positives, false positives, true negatives and false negatives, the source of most classification metrics."),
        ],
        "qa": [
            ("What is the F1 score?", "The balance (harmonic mean) of precision and recall. Useful when you need a single number for imbalanced data."),
            ("What does ROC-AUC measure?", "How well the model ranks positives above negatives across all thresholds. 0.5 is random guessing; 1.0 is perfect."),
            ("How do you pick a classification threshold?", "Based on the business cost of false positives versus false negatives, often using the precision-recall curve."),
        ],
    },
    "Unsupervised Learning": {
        "simple": [
            ("Unsupervised learning", "Find patterns in data without labelled answers, like grouping customers by behaviour."),
            ("k-means", "Pick k centres, assign each point to its nearest centre, move the centres to the middle of their groups, and repeat."),
            ("Choosing k", "Try several values and look at the 'elbow' where adding clusters stops helping much, or use the silhouette score."),
            ("DBSCAN", "Groups points that are densely packed and labels lonely points as outliers. It finds odd-shaped clusters."),
            ("PCA", "Compresses many columns into a few 'summary' directions that keep most of the information, which helps visualisation and speed."),
        ],
        "qa": [
            ("Why scale data before k-means?", "k-means uses distance, so a column measured in thousands would dominate one measured in single digits."),
            ("How would you evaluate clusters without labels?", "Silhouette score, checking that clusters are stable across runs, and whether they make business sense."),
            ("What's a use case for anomaly detection?", "Spotting fraudulent transactions, faulty sensors or unusual server behaviour that doesn't fit normal patterns."),
        ],
    },
    "A/B Testing in Practice": {
        "simple": [
            ("What an A/B test is", "Show version A to some users and version B to others at random, then compare results. Randomness makes it a fair comparison."),
            ("Primary metric", "Decide in advance the one number that defines success, such as checkout conversion."),
            ("Sample size", "Calculate how many users you need before starting. Too few and you can't trust the result."),
            ("Don't peek", "Checking results every day and stopping when it 'looks good' greatly increases false wins."),
            ("Guardrail metrics", "Numbers that must not get worse, like page speed or unsubscribes, even if the main metric improves."),
        ],
        "qa": [
            ("What is the novelty effect?", "Users click new things just because they're new. Run tests long enough (often 2+ weeks) for the effect to fade."),
            ("What's a sample ratio mismatch?", "When the split isn't what you planned (for example 50/50 became 45/55). It signals a bug, and the results can't be trusted."),
            ("Your test is inconclusive. What do you do?", "Check the power and duration, look at segments carefully (avoid fishing), and either extend the test or accept no meaningful difference."),
        ],
    },
    "ML Case Studies": {
        "simple": [
            ("Start from the business goal", "What decision will the model help make? That shapes everything else."),
            ("Define the label", "Be precise, for example 'churned = no activity for 30 days', and decide when you'd know it."),
            ("Baseline", "Start with a simple model or rule, so you know whether the fancy model is actually better."),
            ("Offline vs online", "Good test scores don't guarantee real impact. Measure the business result with an experiment after launch."),
            ("Monitoring", "Data changes over time. Track model performance and input data after deployment and retrain when it drifts."),
        ],
        "qa": [
            ("How would you build a recommendation system for an online store?", "Start with popular and 'bought together' items, then collaborative filtering or embeddings based on user behaviour; evaluate with click and purchase rates in an A/B test."),
            ("How would you detect fraudulent transactions?", "Label past fraud, engineer behavioural features (amount, location, speed), handle class imbalance, optimise recall at an acceptable false-alarm rate, and keep human review."),
            ("What would you do if the model is accurate but nobody uses it?", "Talk to users, make predictions explainable and actionable, and integrate them into existing tools and workflows."),
        ],
    },
    "SQL Querying & Aggregation": {
        "simple": [
            ("SELECT and WHERE", "SELECT picks columns, FROM picks the table, WHERE filters rows: 'show name and city for customers in Delhi'."),
            ("ORDER BY and LIMIT", "Sort results and keep only the top few, such as the 5 highest-value orders."),
            ("GROUP BY", "Groups rows and summarises each group: total sales per region."),
            ("HAVING", "Filters groups after GROUP BY: regions with total sales above 1 lakh."),
            ("JOIN", "Combine tables using a shared key, such as orders with customers, to answer richer questions."),
        ],
        "qa": [
            ("What's the order SQL runs a query in?", "FROM and JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT. That's why you can't use a SELECT alias in WHERE."),
            ("COUNT(*) vs COUNT(column)?", "COUNT(*) counts all rows; COUNT(column) counts only rows where that column isn't NULL."),
            ("How do you find duplicate emails?", "SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;"),
        ],
    },
    "Advanced SQL: CTEs & Window Functions": {
        "simple": [
            ("CTE", "WITH name AS (...) creates a named step, so complex queries read like a recipe instead of nested brackets."),
            ("Window functions", "Calculations across related rows while keeping every row, such as each employee's salary next to their department's average."),
            ("ROW_NUMBER and RANK", "Number rows within each group, which is perfect for 'top 3 products per category'."),
            ("LAG and LEAD", "Look at the previous or next row, for example to compare this month's sales with last month's."),
            ("Running totals", "SUM(...) OVER (ORDER BY date) gives a cumulative total row by row."),
        ],
        "qa": [
            ("RANK vs DENSE_RANK vs ROW_NUMBER?", "With ties, RANK skips numbers (1,1,3), DENSE_RANK doesn't (1,1,2), and ROW_NUMBER gives unique numbers anyway (1,2,3)."),
            ("Get each customer's first order.", "Use ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) in a CTE and keep rows where it equals 1."),
            ("Compute month-over-month growth.", "Aggregate by month in a CTE, then (revenue − LAG(revenue)) / LAG(revenue) OVER (ORDER BY month)."),
        ],
    },
    "Linear Algebra & Calculus Essentials": {
        "simple": [
            ("Vectors", "A list of numbers describing something, like a point in space or a person's features (age, height, income)."),
            ("Matrices", "Grids of numbers. A neural network layer is basically 'multiply the input by a matrix, then add a bias'."),
            ("Dot product", "Multiply matching entries and add them up. It measures how similar or aligned two vectors are."),
            ("Derivative", "How fast something changes, like the slope of a hill under your feet."),
            ("Chain rule", "How to find the slope of a function inside another function. Backpropagation is the chain rule applied layer by layer."),
        ],
        "qa": [
            ("Why do we need gradients in ML?", "The gradient points uphill on the loss. Stepping the opposite way reduces the error, and that's how models learn."),
            ("What are eigenvectors used for in ML?", "In PCA, the top eigenvectors of the covariance matrix are the directions where the data varies most."),
            ("Why do matrix shapes matter?", "Multiplying requires matching inner dimensions, (batch × features) · (features × units), and most beginner bugs are shape mismatches."),
        ],
    },
    "Optimisation & Gradient Descent": {
        "simple": [
            ("Loss function", "A score of how wrong the model is. Training means making this number smaller."),
            ("Gradient descent", "Like walking down a foggy hill: feel the slope, take a step downhill, and repeat until you reach the bottom."),
            ("Learning rate", "The step size. Too big and you overshoot; too small and training takes forever."),
            ("Mini-batches", "Instead of using all data per step, use small batches. It's faster and the noise even helps escape bad spots."),
            ("Adam", "A popular optimiser that adapts the step size for each weight automatically, usually a good default."),
        ],
        "qa": [
            ("What happens if the learning rate is too high?", "The loss jumps around or explodes instead of decreasing, because each step overshoots the minimum."),
            ("What is early stopping?", "Stop training when validation loss stops improving, to avoid overfitting."),
            ("Why use cross-entropy loss for classification?", "It heavily punishes confident wrong predictions and works well with probabilities from softmax or sigmoid."),
        ],
    },
    "Neural Networks & PyTorch": {
        "simple": [
            ("Neurons and layers", "Each neuron combines its inputs with weights and passes the result through an activation. Stacking layers lets the network learn complex patterns."),
            ("Activation functions", "Non-linear functions like ReLU let networks learn curves, not just straight lines."),
            ("Training loop", "Forward pass (predict) → compute loss → backward pass (gradients) → optimiser step (update weights). Repeat."),
            ("Overfitting fixes", "Dropout randomly switches neurons off during training; weight decay keeps weights small; more data helps most."),
            ("GPUs", "GPUs do many multiplications in parallel, which is why deep learning trains much faster on them."),
        ],
        "qa": [
            ("Why call optimizer.zero_grad()?", "PyTorch adds up gradients by default; without zeroing them, each step would mix in gradients from previous batches."),
            ("What does model.eval() change?", "It switches layers like dropout and batch norm to inference behaviour, so predictions are consistent."),
            ("How do you debug a model that won't learn?", "Try to overfit a tiny batch first; check the data and labels, learning rate, loss function and that gradients are flowing."),
        ],
    },
    "CNNs & Computer Vision": {
        "simple": [
            ("Convolution", "A small filter slides over the image looking for a pattern, like an edge or a texture, wherever it appears."),
            ("Feature hierarchy", "Early layers find edges, middle layers find shapes, and deep layers recognise objects like faces or cars."),
            ("Pooling", "Shrinks feature maps by keeping the strongest signals, which reduces computation and adds a bit of position tolerance."),
            ("Transfer learning", "Start from a model already trained on millions of images and fine-tune it on your smaller dataset."),
            ("Data augmentation", "Create extra training images by flipping, rotating or cropping, so the model generalises better."),
        ],
        "qa": [
            ("Why are CNNs better than dense networks for images?", "They reuse the same small filters across the image (far fewer weights) and capture local spatial patterns."),
            ("What problem do residual connections (ResNet) solve?", "They let gradients flow through shortcuts, making very deep networks trainable without vanishing gradients."),
            ("How would you build an image classifier with only 500 images?", "Use transfer learning from a pre-trained model, strong augmentation, and careful validation."),
        ],
    },
    "Transformers & Attention": {
        "simple": [
            ("Attention", "Each word looks at every other word and decides how much each matters for understanding it, like 'it' paying attention to 'the cat'."),
            ("Query, key, value", "Each word asks a question (query), offers a label (key) and carries information (value). Matching queries to keys decides whose values to blend."),
            ("Parallel processing", "Unlike older RNNs that read word by word, Transformers look at all words at once, which trains much faster."),
            ("Positional encoding", "Since all words are processed together, extra information is added so the model knows word order."),
            ("Encoder vs decoder", "Encoders (like BERT) understand text; decoders (like GPT) generate text one token at a time."),
        ],
        "qa": [
            ("What is multi-head attention?", "Several attention operations in parallel, each learning a different kind of relationship (grammar, meaning, position), then combined."),
            ("Why is attention expensive for long texts?", "Every token attends to every other token, so cost grows with the square of the sequence length."),
            ("What is tokenisation?", "Splitting text into pieces (words or sub-words) the model can turn into numbers. 'unbelievable' might become 'un', 'believ', 'able'."),
        ],
    },
    "Prompt Engineering & LLM APIs": {
        "simple": [
            ("Be specific", "Tell the model the task, audience, format and length. Vague prompts get vague answers."),
            ("Few-shot examples", "Show one or two examples of the input and output you want; the model copies the pattern."),
            ("System prompt", "Sets the model's role and rules for the whole conversation, such as 'You are a helpful tutor; answer in simple words'."),
            ("Temperature", "Controls randomness: low for factual or consistent answers, higher for creative writing."),
            ("Structured output", "Ask for JSON with named fields when your code needs to read the answer, and validate it."),
        ],
        "qa": [
            ("What is a hallucination?", "When the model confidently states something false. Reduce it by grounding answers in provided sources (RAG) and asking it to say 'I don't know'."),
            ("What is function or tool calling?", "The model returns a structured request to call a function you defined (like get_weather(city)); your code runs it and sends back the result."),
            ("How do you evaluate prompt quality?", "Build a small test set of real inputs with expected outputs, and compare prompt versions on accuracy and consistency."),
        ],
    },
    "Retrieval-Augmented Generation (RAG)": {
        "simple": [
            ("The problem", "LLMs don't know your private or recent documents and may make things up about them."),
            ("The idea", "Search your documents for relevant passages, put them in the prompt, and ask the model to answer only from them."),
            ("Chunking", "Split documents into small, meaningful pieces (paragraphs or sections) so search returns focused results."),
            ("Embeddings", "Turn text into lists of numbers where similar meanings sit close together, enabling 'search by meaning'."),
            ("Vector database", "Stores embeddings and quickly finds the closest ones to a question (FAISS, Pinecone, pgvector)."),
        ],
        "qa": [
            ("How do you improve poor RAG answers?", "Improve chunking, use hybrid keyword + vector search, add a re-ranker, include metadata filters, and test with a question set."),
            ("RAG vs fine-tuning?", "RAG adds knowledge at question time (easy to update, citable). Fine-tuning changes the model's behaviour or style. Many systems use both."),
            ("How do you show sources in a RAG app?", "Keep document IDs and links with each chunk, pass them into the prompt, and ask the model to cite them."),
        ],
    },
    "Fine-tuning & LoRA": {
        "simple": [
            ("Fine-tuning", "Further training a pre-trained model on your own examples so it adopts a style, format or specialised skill."),
            ("When to fine-tune", "When prompting and RAG aren't enough, you need consistent output, or you want a smaller, cheaper model to do a narrow task well."),
            ("LoRA", "Instead of updating billions of weights, train small add-on matrices. This saves huge amounts of memory and time."),
            ("Data quality", "A few hundred clean, consistent examples beat thousands of messy ones."),
            ("Evaluation", "Always compare against the base model on a held-out test set to confirm fine-tuning actually helped."),
        ],
        "qa": [
            ("What is QLoRA?", "LoRA applied to a model stored in 4-bit precision, so you can fine-tune large models on a single consumer GPU."),
            ("What is catastrophic forgetting?", "The model losing general abilities after fine-tuning on narrow data. Mix in general data or use parameter-efficient methods."),
            ("How much data do you need to fine-tune?", "It depends on the task; for style or format, a few hundred to a few thousand high-quality examples is often enough."),
        ],
    },
    "Model Deployment & Serving": {
        "simple": [
            ("Batch vs real-time", "Batch scores lots of data on a schedule (nightly). Real-time answers each request instantly through an API."),
            ("Packaging", "Ship the model together with its preprocessing so training and serving transform data identically."),
            ("Serving API", "Wrap the model in a web API (FastAPI, TorchServe, vLLM for LLMs) behind a load balancer."),
            ("Versioning", "Track which model version, code and data produced each prediction, so you can roll back."),
            ("Safe rollout", "Run a new model in shadow mode or on a small slice of traffic before switching fully."),
        ],
        "qa": [
            ("How do you reduce model latency?", "Batch requests, use quantisation or smaller models, cache frequent results, and use GPUs or optimised runtimes."),
            ("What is training-serving skew?", "When features are computed differently in training and production, so the model sees different data and performs worse."),
            ("How do you serve an LLM cheaply?", "Use a smaller or quantised model where possible, continuous batching, caching, and route easy questions to cheaper models."),
        ],
    },
    "Monitoring & Drift": {
        "simple": [
            ("Why monitor", "The world changes, so a model that worked last month can silently get worse."),
            ("Data drift", "The inputs change, for example a new type of customer starts using the product."),
            ("Concept drift", "The relationship changes, for example fraudsters change their tactics so old patterns no longer apply."),
            ("What to track", "Input distributions, prediction distributions, accuracy when labels arrive, and business metrics."),
            ("Retraining", "Retrain on fresh data when monitoring shows decline, ideally with automated pipelines and a human check."),
        ],
        "qa": [
            ("How can you detect drift without labels?", "Compare current input and prediction distributions with the training data using statistics like PSI or KS tests."),
            ("How often should you retrain?", "Based on how fast your data changes: monitor and retrain when performance drops, rather than on a fixed schedule only."),
            ("What should trigger an alert?", "Large distribution shifts, sudden changes in prediction rates, rising error rates, or drops in business metrics."),
        ],
    },
    "Excel Formulas & Pivot Tables": {
        "simple": [
            ("Cell references", "A1 is relative (moves when copied); $A$1 is absolute (stays fixed). Mixing them saves lots of typing."),
            ("Lookups", "XLOOKUP (or VLOOKUP / INDEX-MATCH) finds a value in another table, like fetching a product's price by its ID."),
            ("Conditional sums", "SUMIFS and COUNTIFS add or count rows that meet conditions: total sales in March for the North region."),
            ("Pivot tables", "Drag-and-drop summaries: turn thousands of rows into totals by month and region in seconds."),
            ("Tables", "Format data as a Table (Ctrl+T) so formulas and pivots expand automatically when you add rows."),
        ],
        "qa": [
            ("Why is XLOOKUP better than VLOOKUP?", "It can look left or right, doesn't break when columns move, and has built-in 'not found' handling."),
            ("How do you remove duplicates in Excel?", "Data → Remove Duplicates, or use the UNIQUE() function to get a de-duplicated list."),
            ("How would you highlight values above target?", "Conditional formatting with a rule like 'cell value > target cell', with an absolute reference to the target."),
        ],
    },
    "Power BI / Tableau Dashboards": {
        "simple": [
            ("Data model", "Connect tables properly: a central fact table (sales) linked to dimension tables (date, product, customer)."),
            ("Measures", "Calculations like total revenue or conversion rate defined once and reused across visuals."),
            ("Visual hierarchy", "Put the most important KPIs at the top left, then trends, then details."),
            ("Interactivity", "Filters, slicers and drill-downs let people explore without needing new reports."),
            ("Trust", "Check every number against the source system before sharing; one wrong number ruins trust."),
        ],
        "qa": [
            ("Calculated column vs measure in Power BI?", "A calculated column is computed per row and stored; a measure is computed on the fly based on filters. Prefer measures for aggregations."),
            ("How do you make a dashboard fast?", "Use a clean star schema, reduce visuals per page, pre-aggregate large data and avoid complex row-by-row calculations."),
            ("How do you design for executives vs analysts?", "Executives need a few KPIs with trends and targets; analysts need filters, details and the ability to drill down."),
        ],
    },
    "Data Storytelling": {
        "simple": [
            ("Lead with the answer", "Start with the key insight, then show the evidence. Busy people may only read the first line."),
            ("Context", "Numbers mean little alone. Compare them with last month, the target or competitors."),
            ("Right chart", "Bars compare, lines show trends, scatter plots show relationships. Avoid 3D and crowded pie charts."),
            ("Highlight", "Use colour to draw attention to the one thing that matters; grey out the rest."),
            ("Recommendation", "End with what to do next and the expected impact."),
        ],
        "qa": [
            ("How do you explain a complex analysis to non-technical stakeholders?", "Use plain language, one clear chart per point, real examples, and focus on decisions and impact rather than methods."),
            ("What makes a chart misleading?", "Truncated axes, inconsistent scales, cherry-picked time ranges, or 3D effects that distort size."),
            ("How do you handle a finding that contradicts what leadership expects?", "Double-check the data, present the evidence calmly with context, and suggest a way to verify, such as an experiment."),
        ],
    },
    "KPIs, Funnels & Cohorts": {
        "simple": [
            ("KPI", "A key performance indicator: a number that shows whether the business is reaching its goal, like monthly active users."),
            ("Funnel", "The steps users take, such as visit → sign up → purchase. Find the step where most people drop off."),
            ("Retention", "How many users keep coming back over time. Usually more important than sign-ups."),
            ("Cohorts", "Group users by when they started (the January cohort) and track each group separately to see real trends."),
            ("Unit economics", "Customer acquisition cost (CAC) vs lifetime value (LTV): are customers worth more than they cost to get?"),
        ],
        "qa": [
            ("How would you measure the success of a new feature?", "Define the goal, pick a primary metric (such as adoption or retention) plus guardrails, and run an A/B test if possible."),
            ("What's the difference between DAU and MAU?", "Daily vs monthly active users. DAU/MAU (stickiness) shows how often users return."),
            ("Why look at cohorts instead of overall retention?", "Overall numbers mix old loyal users with new ones; cohorts reveal whether newer users retain better or worse."),
        ],
    },
    "Analytics Case Interviews": {
        "simple": [
            ("Clarify", "Ask what exactly changed, since when, how it's measured and why it matters."),
            ("Check the data", "First rule out tracking bugs or pipeline failures; many 'drops' are data problems."),
            ("Segment", "Split by region, platform, user type and channel to find where the change happens."),
            ("Hypotheses", "List likely causes (a release, pricing, seasonality, a competitor) and test them one by one."),
            ("Recommend", "Finish with a clear recommendation and how you'd confirm it."),
        ],
        "qa": [
            ("Sign-ups dropped 20% yesterday. What do you check first?", "Data collection (tracking or pipeline), then whether it's limited to a platform, region or channel, then any releases or outages."),
            ("How would you estimate the number of food delivery orders in a city per day?", "Population × share of online-ordering households × order frequency per week ÷ 7, sanity-checked against known benchmarks."),
            ("What metrics would you track for a ride-sharing app?", "Rides per day, rider retention, driver supply and utilisation, wait time, cancellation rate, and revenue per ride."),
        ],
    },
}
