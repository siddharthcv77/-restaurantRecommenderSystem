var checkout = {}

$(document).ready(function () {
  var $messages = $('.messages-content'),
    d,
    h,
    m,
    i = 0

  $(window).load(function () {
    $messages.mCustomScrollbar()
    insertResponseMessage(
      "Hello! If you’re a returning user, please enter your email address. Otherwise, type 'continue' to proceed.",
    )
  })

  function updateScrollbar() {
    $messages
      .mCustomScrollbar('update')
      .mCustomScrollbar('scrollTo', 'bottom', {
        scrollInertia: 10,
        timeout: 0,
      })
  }

  function setDate() {
    d = new Date()
    if (m != d.getMinutes()) {
      m = d.getMinutes()
      $('<div class="timestamp">' + d.getHours() + ':' + m + '</div>').appendTo(
        $('.message:last'),
      )
    }
  }

  // Modified function to send the message in the correct format
  function callChatbotApi(message) {
    // Send the message as `userMessage` to match the Lambda's expectation
    return sdk.chatbotPost(
      {},
      {
        userMessage: message, // Send message as userMessage
      },
      {},
    )
  }

  function insertMessage() {
    msg = $('.message-input').val()
    if ($.trim(msg) == '') {
      return false
    }
    $('<div class="message message-personal">' + msg + '</div>')
      .appendTo($('.mCSB_container'))
      .addClass('new')
    setDate()
    $('.message-input').val(null)
    updateScrollbar()

    callChatbotApi(msg)
      .then((response) => {
        console.log(response)
        var data = response.data

        if (data && data.body) {
          try {
            var parsedBody = JSON.parse(data.body)
            if (parsedBody.message) {
              insertResponseMessage(parsedBody.message)
            } else {
              insertResponseMessage(
                'Received an empty response from the server.',
              )
            }
          } catch (error) {
            console.error('Error parsing response:', error)
            insertResponseMessage(
              'Oops, something went wrong while processing the response.',
            )
          }
        } else {
          insertResponseMessage('Oops, something went wrong. Please try again.')
        }
      })
      .catch((error) => {
        console.log('an error occurred', error)
        insertResponseMessage('Oops, something went wrong. Please try again.')
      })
  }

  $('.message-submit').click(function () {
    insertMessage()
  })

  $(window).on('keydown', function (e) {
    if (e.which == 13) {
      insertMessage()
      return false
    }
  })

  function insertResponseMessage(content) {
    $(
      '<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>',
    ).appendTo($('.mCSB_container'))
    updateScrollbar()

    setTimeout(function () {
      $('.message.loading').remove()
      $(
        '<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' +
          content +
          '</div>',
      )
        .appendTo($('.mCSB_container'))
        .addClass('new')
      setDate()
      updateScrollbar()
      i++
    }, 500)
  }
})
