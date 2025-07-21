import streamlit as st
import os

# Define learning content sections
learning_content = [
    {
        "title": "Welcome to Dyce Energy Training",
        "content": "Welcome to the Dyce Energy Gas Billing Training. In this course, you'll gain an understanding of the fundamentals of gas billing, including meter reads, MPRNs, standing charges, Climate Change Levy (CCL), and VAT. By the end, you'll be confident in handling basic customer queries and interpreting bills.",
        "image": "images/Dyce-logo.png"
    },
    {
        "title": "Overview of Gas Billing",
        "content": "Energy billing can seem complex, but it's all about two main charges: \n- Unit Rate: The cost per kWh of gas used.\n- Standing Charge: A daily charge for the meter and associated network costs.\nMeter reads determine consumption, which is converted to kWh for billing.",
        "image": "images/overview.jpg"
    },
    {
        "title": "Understanding MPRN",
        "content": "MPRN stands for Meter Point Reference Number. It's a unique identifier for every gas meter, crucial for ensuring the right meter is billed.",
        "image": "images/read.jpg"
    },
    {
        "title": "Types of Meter Reads",
        "content": "There are several types of reads used in gas billing:\n- O: Opening Read\n- E: Estimated Read\n- C: Customer Read\n- A: Agent Read\n- RR: Reconcile Read\n- COR: Corrected Opening Read",
        "image": "images/readtype.jpg"
    },
    {
        "title": "Climate Change Levy (CCL)",
        "content": "CCL is a government-imposed tax on non-domestic energy use, calculated per kWh used. The rate changes yearly, and usage below certain thresholds can be exempt.",
        "image": "images/ccl.jpg"
    }
]

# Quiz Data
quiz_questions = [
    {
        "question": "What does MPRN stand for?",
        "options": [
            "Meter Point Reference Number",
            "Monthly Price Rate Number",
            "Meter Period Reference Node"
        ],
        "answer": "Meter Point Reference Number",
        "image": "images/read.jpg",
        "explanation": "MPRN stands for Meter Point Reference Number. It's the unique identifier for a gas meter."
    },
    {
        "question": "Which read type is submitted by a customer?",
        "options": [
            "A - Agent Read",
            "C - Customer Read",
            "E - Estimated Read"
        ],
        "answer": "C - Customer Read",
        "image": "images/readtype.jpg",
        "explanation": "'C' stands for Customer Read – provided directly by the customer."
    }
]

def main():
    st.title("Dyce Energy - Gas Billing Training")
    if os.path.exists("images/Dyce-logo.png"):
        st.image("images/Dyce-logo.png", width=200)

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ['Training Content', 'Quiz'])

    if page == 'Training Content':
        show_learning_content()
    elif page == 'Quiz':
        show_quiz()

def show_learning_content():
    for section in learning_content:
        st.header(section['title'])
        st.write(section['content'])
        if 'image' in section and os.path.exists(section['image']):
            st.image(section['image'], use_column_width=True)
        st.markdown("---")

def show_quiz():
    st.header("Knowledge Check Quiz")
    score = 0

    for idx, q in enumerate(quiz_questions):
        st.subheader(f"Question {idx + 1}")
        if os.path.exists(q['image']):
            st.image(q['image'], use_column_width=True)
        user_choice = st.radio(q['question'], q['options'], key=idx)

        if user_choice == q['answer']:
            st.success("Correct!")
            score += 1
        else:
            st.error("Incorrect.")

        st.info(f"Explanation: {q['explanation']}")
        st.markdown("---")

    st.subheader(f"Final Score: {score} / {len(quiz_questions)}")
    st.progress(score / len(quiz_questions))

if __name__ == '__main__':
    main()
