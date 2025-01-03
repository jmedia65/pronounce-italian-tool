$(document).ready(function () {
  function translateText() {
    const text = $("#input-text").val();
    const sourceLanguage = $("#source-language").val();

    if (text.trim() === "") {
      alert("Please enter some text to translate.");
      return;
    }

    $.ajax({
      type: "POST",
      url: "/translate-now",
      contentType: "application/json",
      data: JSON.stringify({
        text: text,
        source_language: sourceLanguage,
      }),
      success: function (response) {
        if (response.translatedTextItalian) {
          $("#translated-text").html(`${response.translatedTextItalian}`);
          // $("#translated-text").text(response.translatedTextItalian);
          if (response.phonetics) {
            $("#phonetics-text").html(`${response.phonetics}`);
          }
          $("#audio-container").show();
          // Remove all audio-related code from here
        } else {
          console.error("Translation failed");
        }
      },
      error: function (xhr) {
        // Parse the error message from the response
        const errorMessage =
          xhr.responseJSON?.error || "An error occurred during translation";

        // Display error message to user
        $("#error-message").html(
          `<div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${errorMessage}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>`
        );
      },
    });
  }

  $("#translate-button").click(function () {
    translateText();
  });
});
