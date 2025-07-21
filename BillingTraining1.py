import streamlit as st

# Define learning content sections
learning_content = [
    {
        "title": "Welcome to Dyce Energy Training",
        "content": "In this course, you'll learn the basics of Gas Billing including MPRNs, Read Types, CCL, VAT, and Standing Charges.",
        "image": "images/Dyce-logo.png"
    },
    {
        "title": "What is an MPRN?",
        "content": "MPRN stands for Meter Point Reference Number. It's the unique identifier for a gas meter and is crucial for billing accuracy.",
        "image": "images/read.jpg"
    },
    {
        "title": "Read Types",
        "content": "There are different types of meter reads: \n- O: Opening Read \n- E: Estimated Read \n- C: Customer Read \n- A: Agent Read",
        "image": "images/readtype.jpg"
    },
    {
        "title": "What is the CCL?",
        "content": "Climate Change Levy (CCL) is a tax on non-domestic energy use, calculated per kWh used.",
        "image": "images/ccl.jpg"
    }
]

# Sample quiz data
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
        "explanation": "MPRN stands for Meter Point Reference Number. It's the unique ID for a gas meter."
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
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ['Welcome & Training Content', 'Quiz'])

    if page == 'Welcome & Training Content':
        show_learning_content()
    elif page == 'Quiz':
        show_quiz()

def show_learning_content():
    for section in learning_content:
        st.header(section['title'])
        st.write(section['content'])
        if 'image' in section:
            st.image(section['image'], use_column_width=True)
        st.markdown("---")

def show_quiz():
    st.header("Knowledge Check Quiz")
    score = 0

    for idx, q in enumerate(quiz_questions):
        st.subheader(f"Question {idx + 1}")
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
