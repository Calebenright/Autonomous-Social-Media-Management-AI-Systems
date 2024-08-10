from django.urls import path
from . import views

app_name = 'service'

urlpatterns = [
    path("getting-started/", views.getting_started, name="getting_started"),
    path("getting-started-success/", views.getting_started_success, name="getting_started_success"),
    path("ftue/", views.ftue, name="ftue"),
    path("choose-images/", views.choose_images, name="choose_images"),
    path("social_media/", views.social_media, name="social_media"),
    path("content-creator/", views.content_creator, name="content_creator"),
    path("graphic-designer/", views.graphic_designer, name="graphic_designer"),
    path("video-editor/", views.video_editor, name="video_editor"),
    path("advertising-specialist/", views.advertising_specialist, name="advertising_specialist"),
    path("settings/", views.settings, name="settings"),
    path("calendar/", views.calendar, name="calendar"),
    path("library/", views.library, name="library"),
    path("advertising-checkout/", views.advertising_checkout, name="advertising_checkout"),
    path("checkout/", views.checkout, name="checkout"),
    path("social-auth/", views.social_auth, name="social_auth"),
    path("download/", views.download, name="download"),
    path("unlink/", views.unlink, name="unlink"),
    path("submit-brief/", views.submit_brief, name="submit_brief"),
    path("generate-signed_url/", views.generate_signed_url, name="generate_signed_url"),
    path("make-file-public/", views.make_file_public, name="make_file_public"),
    path("process-page-selection/", views.process_page_selection, name="process_page_selection"),
]