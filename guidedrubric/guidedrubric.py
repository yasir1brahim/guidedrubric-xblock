"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
import openai
from typing_extensions import override
from openai import AssistantEventHandler
from dotenv import load_dotenv
import time
import re
import json


load_dotenv()
client = openai.OpenAI()
model = "gpt-4-turbo-preview"

ai_messages = []
ai_grade = []
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.

class EventHandler(AssistantEventHandler):    
  def __init__(self, grade=False):
        super().__init__()
        self.grade = grade
  @override
  def on_text_created(self, text) -> None:
    pass
    # print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    if delta.value:
        if self.grade:
            ai_grade.append(delta.value)
        else:
            ai_messages.append(delta.value)
      
  def on_tool_call_created(self, tool_call):
    pass
    # print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)
 
# Then, we use the `create_and_stream` SDK helper 
# with the `EventHandler` class to create the Run 
# and stream the response.

phases = [
    {
        "id": "name",
        "question": """What is your name?""",
        "sample_answer": "",
        "instructions": """The user will give you their name. Then, welcome the user to the exercise, and explain that you'll help them and provide feedback as they go. End your statement with "I will now give you your first question about the article." """,
        "rubric": """
            1. Name
                    1 point - The user has provided a response in this thread. 
                    0 points - The user has not provided a response. 
        """,
        "label": "GO!",
        "minimum_score": 0
    },
    {
        "id": "about",
        "question": """What is the article about?""",
        "sample_answer":"This article investigates the impact of various video production decisions on student engagement in online educational videos, utilizing data from 6.9 million video watching sessions on the edX platform. It identifies factors such as video length, presentation style, and speaking speed that influence engagement, and offers recommendations for creating more effective educational content.",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
                1. Length
                    1 point - Response is greater than or equal to 150 characters.
                    0 points - Response is less than 150 characters. 
                2. Key Points
                    2 points - The response mentions both videos AND student engagement rates
                    1 point - The response mentions either videos OR student engagement rates, but not both
                    0 points - The response does not summarize any important points in the article. 
        """,
        "minimum_score": 2
    },
    {
       "id": "methdologies",
       "question": "Summarize the methodology(s) used.",
       "sample_answer": "The study gathered data around video watch duration and problem attempts from the edX logs. These metrics served as a proxy for engagement. Then it compared that with video attributes like length, speaking rate, type, and production style, to determine how video production affects engagement.",
       "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
       "rubric": """
               1. Correctness
                   1 point - Response is correct and based on facts in the paper
                   0 points - Response is incorrect or not based on facts in the paper
               """,
       "minimum_score": 1
    },
    {
        "id": "findings",
        "question": "What were the main findings in the article?",
        "sample_answer": "Shorter videos are more engaging; Faster-speaking instructors hold students' attention better; High production value does not necessarily correlate with higher engagement;",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
            1. Correctness
                    2 points - Response includes two or more findings or recommendations from the study
                    1 point - Response includes only one finding or recommendation form the study
                    0 points - Response includes no findings or recommendations or is not based on facts in the paper
                    """,
        "minimum_score": 1
    },
    {
        "id": "limitations",
        "question": "What are some of the weaknesses of this study?",
        "sample_answer": "The study cannot measure true student engagement, and so it must use proxies; The study could not track any offline video viewing; The study only used data from math/science courses;",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
            1. Correctness
                    2 points - Response includes two or more limitations of the study
                    1 point - Response includes only one limitation in the study
                    0 points - Response includes no limitations or is not based on facts in the paper
                2. Total Score
                    The total sum of their scores. 
            """,
        "minimum_score": 1
    }
    #Add more steps as needed
    
]

session_state = {
    "current_question_index": 0,
    "thread_obj": None,
    # Add more session state variables as needed
}

current_question_index = session_state['current_question_index'] if 'current_question_index' in session_state else 0

class AssistantManager:
    thread_id = ""
    assistant_id = "asst_BFlYa2t1svtMFaGbMkB4QuMp"


    if 'current_question_index' not in session_state:
        session_state.thread_obj = []


    def __init__(self, model: str = model):
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Retrieve existing assistant and thread if IDs are already set
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name, instructions=instructions, tools=tools, model=self.model
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"AssisID:::: {self.assistant.id}")

    def create_thread(self):
        if not self.thread:
            if session_state['thread_obj']:
                print(f"Grabbing existing thread...")
                thread_obj = session_state['thread_obj']
            else:
                print(f"Creating and saving new thread")
                thread_obj = self.client.beta.threads.create()
                session_state['thread_obj'] = thread_obj

            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"ThreadID::: {self.thread.id}")

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id, role=role, content=content
            )

    def run_assistant(self, instructions, grade):
        if self.thread and self.assistant:
            try:
                with self.client.beta.threads.runs.create_and_stream(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id,
                    instructions=instructions,
                    event_handler=EventHandler(grade=grade),
                ) as stream:
                    stream.until_done()
                    self.run = stream._AssistantEventHandler__current_run
                    self.process_message()
            except Exception as e:
                print(f"Streaming error: {e}")

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []

            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)

            self.summary = "\n".join(summary)
            
    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "respond":
                output = respond(structured_response=arguments["structured_response"])
            
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"], "output": final_str})
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id, run_id=self.run.id, tool_outputs=tool_outputs
        )

    def get_summary(self):
        return self.summary

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id, run_id=self.run.id
                )

                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    self.call_required_functions(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )


def extract_score(text):
    # Define the regular expression pattern
    #regex has been modified to grab the total value whether or not it is returned inside double quotes. The AI seems to fluctuate between using quotes around values and not. 
    pattern = r'"total":\s*"?(\d+)"?'
    
    # Use regex to find the score pattern in the text
    match = re.search(pattern, text)
    
    # If a match is found, return the score, otherwise return None
    if match:
        return int(match.group(1))
    else:
        return 0

def check_score(score, question_num):
    if score >= phases[question_num]["minimum_score"]:
        return True
    else:
        return False

def handle_skip(index):
    session_state[f"phase_{index}_state"] = "skip"
    session_state['current_question_index'] += 1

def build_instructions(index, graded_step=False):
    if graded_step:
        compiled_instructions = """Please provide a score for the previous user message in this thread. Use the following rubric:
        """ + phases[index]["rubric"] + """
        Please output your response as JSON, using this format: { "[criteria 1]": "[score 1]", "[criteria 2]": "[score 2]", "total": "[total score]" }"""
    else:
        compiled_instructions = phases[index]["instructions"] + phases[index]["question"]

    return compiled_instructions

def handle_assistant_grading(index, manager):

    instructions = build_instructions(index, True)
    manager.run_assistant(instructions, True)

    # manager.wait_for_completion()
    summary = manager.get_summary()
    session_state[f"phase_{index}_rubric"] = summary

    score = extract_score(str(summary))
    session_state[f"phase_{index}_score"] = score

    #If the score passes, then increase the index to move to the next step                
    if check_score(score, index):
        session_state['current_question_index'] += 1
        session_state[f"phase_{index}_state"] = "Success"
    else:
        session_state[f"phase_{index}_state"] = "Fail"
    return session_state[f"phase_{index}_state"]

def handle_assistant_interaction(index, manager, user_input):
    manager.add_message_to_thread(
        role="user", content=user_input
    )
    instructions = build_instructions(index)
    manager.run_assistant(instructions, False)
    # manager.wait_for_completion()
    summary = manager.get_summary()
    session_state[f"phase_{index}_summary"] = summary
    return summary

def main(user_input):

    #Create the assistant one time. Only if the Assistant ID is not found, create a new one. 
    manager = AssistantManager()

    manager.create_assistant(
    name="Guided Rubric",
    instructions="""You are a helpful tutor that is guiding a university student through a critical appraisal of a scholarly journal article. You want to encourage the students ideas, but you also want those idea to be rooted in evidence from the journal article that you'll fetch via retrieval. 

Generally, you will be asked to provided feedback on the students answer based on the article, and you'll also sometimes be asked to score the submission based on a rubric which will be provided. More specific instructions will be given in the instructions via the API. 
        """,
    tools=""
    )
    manager.create_thread()
    
    if  session_state['current_question_index'] <= len(phases) - 1:
        index = session_state['current_question_index']
        if user_input == "skip":
            handle_skip(index)
            hand_intr = None
            hand_gra = None
        elif session_state['current_question_index'] <= len(phases):
            hand_intr = handle_assistant_interaction(index, manager, user_input)
            hand_gra = handle_assistant_grading(index, manager)
        try:
            question = phases[session_state['current_question_index']]['question']
        except:
            question = None
        messages_to_send = ai_messages.copy()
        ai_messages.clear()
        return hand_intr, hand_gra, question, messages_to_send

class GuidedRubricXBlock(XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    # TO-DO: delete count, and define your own fields.

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # TO-DO: change this view to display your data your own way.
    def studio_view(self, context=None):
        html = self.resource_string("static/html/guidedrubric.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/guidedrubric.css"))
        frag.add_javascript(self.resource_string("static/js/src/guidedrubric.js"))
        frag.initialize_js('GuidedRubricXBlock')
        return frag

    def student_view(self, context=None):
        """
        The primary view of the GuidedRubricXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/guidedrubric.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/guidedrubric.css"))
        frag.add_javascript(self.resource_string("static/js/src/guidedrubric.js"))
        frag.initialize_js('GuidedRubricXBlock')
        return frag

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def send_message(self, data, suffix=""):
        """Send message to OpenAI, and return the response"""
        user_input = data['message']
        res = main(user_input)
        return {'result': 'success' if res else 'failed', 'response': res}

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("GuidedRubricXBlock",
             """<guidedrubric/>
             """),
            ("Multiple GuidedRubricXBlock",
             """<vertical_demo>
                <guidedrubric/>
                <guidedrubric/>
                <guidedrubric/>
                </vertical_demo>
             """),
        ]
