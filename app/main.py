from scraper import main_scraper as scraper
import asyncio
from db_functions import add_embeddings
from db_functions import get_similar_results
from db_functions import company_crud
from gemini import gemini_functions as gemini
import time


def scrape_and_add_company(company_name):
    start_time = time.time()
    """Main function to scrape and process data for a given company."""
    # Scrape data
    scraped_data = scraper.scrape_data(company_name)
    
    if not scraped_data:
        print(f"No data found for {company_name}.")
        return

    # Process and add embeddings
    for item in scraped_data:
        embeddings = gemini.create_embeddings(item['summary'])
        add_embeddings.insert_post(item['link'], item['summary'], embeddings)

    company_crud.add_company(company_name)
    print(f"Data processing completed for {company_name} in {time.time() - start_time:.2f} seconds.")
    return time.time() - start_time

if __name__ == "__main__":
    company_name = "uber"
    print(scrape_and_add_company(company_name))
    # data = [{'link': 'https://leetcode.com/discuss/post/6972061/meta-software-engineer-machine-learning-edwsu/', 'summary': "I'd be happy to help you summarize the job interview post content.\n\nHere's a concise summary:\n\nThe post provides two separate tasks:\n\n1. Find buildings with an ocean view: A building has an ocean view if any part of it can see the ocean without obstruction. The task takes an array of numbers representing building heights and returns the indexes (or positions) of buildings that meet this condition.\n\n2. Print 2D array elements in diagonal order: The task requires a 2D array input, which is expected to have integer values. It prints out the elements of the array in a specific diagonal order as shown in an image provided.\n\nThe key insights from these tasks are:\n\n- Building heights and their positions can help identify buildings with an ocean view.\n- Diagonal ordering of the 2D array might be required based on specific conditions or requirements, but this is not explicitly stated."}, {'link': 'https://leetcode.com/discuss/post/6884961/meta-variant-for-making-a-large-island-l-ahtw/', 'summary': "Here's a concise summary of the job interview post content:\n\nThe candidate is expressing their aversion to a specific LeetCode problem, LC827 Making a Large Island. This problem is often asked in coding rounds and requires up to 60 lines of code to solve, leaving limited time for other problems. The candidate suggests that this problem can be more efficiently solved with reusable functions and highlights the challenge it poses in terms of code size and compilation efficiency."}, {'link': 'https://leetcode.com/discuss/post/6907624/am-i-a-terrible-software-engineer-need-c-1y4n/', 'summary': "Here's a concise summary of the job interview post:\n\nThe author, a B.Tech CSE graduate, is struggling with disengagement from coding due to unfulfilling work in a US-based bank. They feel that many software engineers they know are not enjoying their roles despite being with top companies like Google and Rubrik. The author wonders if the issue lies with their job, industry, or something deeper.\n\nThey are seeking advice from others who have gone through similar experiences, asking questions about:\n\n* If it's normal to feel unfulfilled in a software engineering role after 3 years\n* Has anyone switched industries or roles and found satisfaction\n* How did they know it was the right move for them\n* Did their decision lead to increased job satisfaction?\n\nThe author hopes to gather insights from others who have faced similar challenges, with the goal of finding a more fulfilling career path in software engineering."}, {'link': 'https://leetcode.com/discuss/post/6988266/meta-e5-product-system-design-interview-sgj7v/', 'summary': 'Here\'s a concise summary of the job interview post:\n\nThe author shared their experience as a Senior Product Engineer (E5) candidate at Meta for an E5+ role. They had two system design rounds, with one test designed to level candidates between Mid-level E4 and Senior E5 roles. The author believes that the second round was more straightforward, but still required significant data points.\n\nTheir key observation is that senior roles often require more data points than mid-level roles to make a decision. In their experience, the two-round interview process helps the hiring committee "down-level" candidates who show strong leveling capabilities upfront, and then extend an offer if they don\'t meet all senior-level criteria.\n\nTo prepare for similar interviews, the author suggests:\n\n1. Master core system design concepts (scaling, latency, availability)\n2. Practice standard individual problems\n3. Combine problems to think about how different systems could be merged\n\nThe author also shares their own approach using a prompt from "hellointerview" to generate plausible combinations of problems, which they found eye-opening and useful for future reference.'}, {'link': 'https://leetcode.com/discuss/post/7001358/looking-for-a-consistent-study-partner-s-lf5t/', 'summary': "Here's a concise summary of the job interview post:\n\nA tech industry professional is seeking a dedicated study partner for upcoming interviews. They are currently preparing for product-based company interviews and have experience with top tech companies such as Google and Meta. The ideal study partner will be from a tech background, committed to continuous learning, problem-solving, and regular collaboration sessions."}, {'link': 'https://leetcode.com/discuss/post/6874512/meta-onsite-awaiting-results-by-codingwi-mo1f/', 'summary': "Here's a concise summary of the job interview post:\n\nThe post shares five job interviews where the candidate had to answer behavioral and system design-related questions. Key points include:\n\n- The candidates were presented with different problem-solving scenarios, such as finding left and right side views in binary trees, removing adjacent duplicates from a list, and merging sorted lists.\n- Questions focused on data structures (trees, queues), algorithmic thinking (BFS, rolling window), system design (proximity server), and leadership skills.\n- The candidate was asked about handling conflicts, demonstrating mentorship experiences, and projects they're most proud of.\n\nThe post does not provide specific details about the candidates' performance or outcomes, leaving room for individual interpretation."}, {'link': 'https://leetcode.com/discuss/post/6869536/meta-variant-for-monotonic-array-lc896-b-6tzj/', 'summary': 'The job post is for a position that deals with solving a Monotonic Array problem from LeetCode 896. The task involves finding and counting strictly increasing, decreasing, and unchanging sequences within an array. The twist is that there are multiple variants of this problem, requiring different conditions to be met.\n\nKey points:\n\n- Solve the Monotonic Array problem from LeetCode 896\n- Find and count strictly increasing, decreasing, and unchanging sequences in an array\n- Different variants of the problem require unique conditions (increasing only, decreasing only, or both)\n- The post emphasizes that this is a relatively niche task and may be asked in phone screens as well'}];



    # create while loop until user types 'exit'
    # while True:
    #     user_query = input("Enter your query (or type 'exit' to quit): ")
    #     if user_query.lower() == 'exit':
    #         break
    #     print(f"User Query: {user_query}")
    #     embeddings = gemini.create_embeddings(user_query)
    #     context_chunks = get_similar_results.search_similar_summaries(embeddings, top_k=5)
    #     model_result = gemini.generate_answer_with_context(user_query, context_chunks)
    #     print(f"Model Result: {model_result}")
    #     print("" + "="*50 + "\n")

    # Run the main function with the company name
