import os
import re

from django import forms
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_POST

from django_docker_engine.docker_utils import (DockerClientRunWrapper,
                                               DockerClientSpec,
                                               DockerContainerSpec)

from .forms import LaunchForm, UploadForm
from .tools import tools
from .utils import hostname

client = DockerClientRunWrapper(
    DockerClientSpec(None, do_input_json_envvar=True))
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')


def index(request):
    launch_form = LaunchForm()
    # TODO: Pass this info through the constructor
    launch_form.fields['data'] = forms.ChoiceField(
        widget=forms.Select,
        choices=((f, f) for f in os.listdir(UPLOAD_DIR) if f != '.gitignore')
    )
    launch_form.initial['data'] = request.GET.get('uploaded')

    context = {
        'container_names': [container.name for container in client.list()],
        'launch_form': launch_form,
        'upload_form': UploadForm(),
    }
    return render(request, 'index.html', context)


@require_POST
def launch(request):
    form = LaunchForm(request.POST)
    if not form.is_valid():
        raise ValidationError('invalid form')

    post = form.cleaned_data

    input_url = 'http://{}:{}/upload/{}'.format(
        hostname(), request.get_port(), post['data'])
    tool_spec = tools[post['tool']]

    container_name = post['container_name']
    container_path = '/docker/{}/'.format(container_name)
    container_spec = DockerContainerSpec(
        container_name=container_name,
        image_name=tool_spec['image'],
        input=tool_spec['input'](input_url, container_path))
    client.run(container_spec)
    return HttpResponseRedirect(container_path)


@require_POST
def kill(request, name):
    container = client.list(filters={'name': name})[0]
    client.kill(container)
    return HttpResponseRedirect('/')


def upload(request, name):
    valid_re = r'^\w+(\.\w+)*$'

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise ValidationError('invalid form')
        file = request.FILES['file']
        assert re.match(valid_re, file.name)
        fullpath = os.path.join(UPLOAD_DIR, file.name)
        with open(fullpath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return HttpResponseRedirect('/?uploaded={}'.format(file.name))

    else:
        assert re.match(valid_re, name)
        fullpath = os.path.join(UPLOAD_DIR, name)
        if not os.path.isfile(fullpath):
            raise Http404()
        else:
            with open(fullpath) as f:
                return HttpResponse(f.read(), content_type='text/plain')
