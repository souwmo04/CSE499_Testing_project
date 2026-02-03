document.addEventListener('DOMContentLoaded', function() {
    const askBtn = document.getElementById('ask-ai-btn');
    const questionInput = document.getElementById('ai-question');
    const answerBox = document.getElementById('ai-answer');

    askBtn.addEventListener('click', function() {
        const question = questionInput.value.trim();
        if (question === "") {
            answerBox.textContent = "Please type a question.";
            return;
        }

        answerBox.textContent = "AI is analyzing the dashboard...";

        setTimeout(() => {
            answerBox.textContent = "Simulated AI Answer: " + question;
        }, 2000);
    });
});
