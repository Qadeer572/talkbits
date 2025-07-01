from django.shortcuts import render

# Create your views here.
def chat_view(request):
    """
    Render the main chat view.
    """
    return render(request, 'chatApp/chat.html')