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
          $("#translated-text").text(response.translatedTextItalian);
          $("#audio-container").show();
          // Remove all audio-related code from here
        } else {
          console.error("Translation failed");
        }
      },
      error: function () {
        console.error("Error in translation request");
      },
    });
  }

  $("#translate-button").click(function () {
    translateText();
  });
});
