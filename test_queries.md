# SQL Agent Test Queries

## Basic Queries

How many customers are in the database?

How many orders have status 'F'?

What is the total number of suppliers?

How many customers are from CHINA?

How many suppliers are from GERMANY?

Show the count of customers in each nation, limit to 5 nations

How many nations are in the database?

How many orders have status 'O'?

Are there more customers or suppliers in the database?

---

## Conversation Memory Tests

### Test 1: Basic Follow-Up
How many customers are there?
What about suppliers?
Which has more?

### Test 2: Pronoun Resolution
How many customers are from CHINA?
What about from UNITED STATES?
Which country has more of them?

### Test 3: Implicit Context
How many nations are in the database?
Show me 5 of them
How many customers are in those nations?

### Test 4: Progressive Filtering
How many orders have status 'F'?
What about status 'O'?
What's the total of both?

### Test 5: Comparison Chain
How many suppliers are from GERMANY?
How many are from FRANCE?
What's the difference?

### Test 6: Derived Calculation
How many customers are there?
How many orders are there?
What's the average number of orders per customer?

### Test 7: Pattern Replication
Show me 3 nations from the database
Do the same for suppliers, limit to 5

### Test 8: Location Context
How many customers are in ASIA region?
What about suppliers in the same region?

### Test 9: Multi-Turn Aggregation
How many customers are from CHINA?
How many customers are from INDIA?
How many customers are from JAPAN?
What's the total across all three countries?

### Test 10: Clarification Request
Are there more customers or suppliers?
What are the exact numbers?

### Test 11: Nested Reference
How many suppliers are in each region? Show top 3
Which region had the most?
How many customers are in that region?
