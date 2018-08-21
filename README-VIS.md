# Visualization author documentation

`django_docker_engine` exists to make web-based visualizations reusable:
If you can wrap your visualization in a container image, and adhere to a few
conventions, your tool will remain useful and usable even when you've moved
on to other projects.

We'll outline here what a container image is and how to build one, what
particular conventions `django_docker_engine` requires, some gotchas to be aware
of, and how to publish your tool. It probably makes the most sense to read this
document quickly once over to get an overview, and then more slowly to get the details.

## Building the image

If you haven't worked with containers before, read this
[introduction to Docker](https://docs.docker.com/get-started/), and try the
examples in this [introcution to containers](https://docs.docker.com/get-started/part2/).
The container ecology is complicated, but you only need to focus on one part,
building your container and pushing it to a repository,
and hopefully you can base your work on one of our examples.

From the introduction, you should have the sense that containers are built up
from layers, and it is important to start with the right first layer.
Any popular language or framework will have a base image you can begin from,
listed at the top of you `Dockerfile`: after that you will add additional
libraries you require, and finally the code for your particular project.
Here are samples from some of our projects:

- [Python](https://github.com/refinery-platform/heatmap-scatter-dash/blob/master/context/Dockerfile)
- [R Shiny](https://github.com/refinery-platform/intervene-refinery-docker/blob/master/context/Dockerfile)
- [JS](https://github.com/refinery-platform/lineup-refinery-docker/blob/master/context/Dockerfile)*

The JS example is odd, because although the real code is JS, a small script to
process the input was required, so the base image is Python.

It is best for your `Dockerfile` to be under version control. You might include
it in the repo for your project, and have Docker builds be
triggered with each check in: This is what we've done in the Python and
Shiny examples above. In other cases, because of build complexity, or because
you're wrapping a third party tool, the real source code will be in a separate
repo that you only reference: When that repo is updated, you'll need to bump
a corresponding version number in your wrapper.

## Inputs

When your container starts up, an `INPUT_JSON_URL` environment variable will be available.
(It is good practice and can make development easier to also check `INPUT_JSON`.)
Its content will look something like [this](https://github.com/refinery-platform/docker_igv_js/blob/master/input_fixtures/good/input.json).
- Input files are provided as a list of URLs under `file_relationships`.
- Detailed metadata for each file in the dataset, not just your input, is provided
in `node_info`.
- User supplied strings or numbers are available in `parameters`.

## Development

To run your container locally, check out this project and add a description of your
tool to `tools.py`, and start the demo with `python ./manage.py runserver`.
The `image` field can reference images either on DockerHub, or in your local cache.

## Gotchas

There are a few things to be careful about when wrapping your tool.

- **Port 80**: `django_docker_engine` assumes your tool will use port 80: If you're using
a different port, that needs to be communicated when you publish your tool.
(See the last section below.)
- **Relocatable**: There will be a prefix in the path when your tool is served.
No URLs you use should begin with `/`... but if you really need to know the 
prefix, it is available in the `api_prefix` of your input.json.
- **Keep the cookies**: Your tool will ultimately be run inside django, so the django
session cookie needs to be preserved on any AJAX requests you make. Right now,
FF and Chrome have slightly different implementations of the HTML5 Fetch API
in this regard.
- **No WebSockets**: WebSockets are a step beyond HTTP, and won't work across plain
HTTP proxies like we use.
- **No server state**: There are no provisions right
now to preserve sessions or to make them available with restarts. Instead, try
to update the query portion of the URL.
- **Logging**: The Docker way to log is simply to output to STDOUT. If any files
are updated or created, they should be listed in the `extra_directories` of your spec:
If there is a lot of writing outside this space, you might exhaust the limited space
dedicated to the container.
- **Friendly error page**: Until your tool has fully started, it should either
not reply, or reply with a non-200 response to requests for `/`. Once it has
started, a 200 should be returned. If your tool can't start for some reason,
it is still good to start a minimal HTTPD and return an error page with a 200
status. (This semantics aren't quite right, but we're doing it this way because
other error codes might be returned by a server which just hasn't fully started.)

## Pushing to DockerHub

DockerHub is the most prominent repository of docker images: It is our source
for base images, and we push our own containerized tools back there as well. Once
you have registered for an account, you could push images by hand, but it is better
to add encrypted credentials to your `.travis.yaml` and have Travis do it for you
on successful tagged builds. Here's a [script](https://github.com/refinery-platform/intervene-refinery-docker/blob/master/after_success.sh)
that many of our projects use.

## Publishing

Once you've pushed your image to DockerHub, you need to let the community know about it.
PRs to this repo which add to `tools.py` are welcome, and you should make a similar
addition to the [list of Refinery tools](https://github.com/refinery-platform/visualization-tools/tree/master/tool-annotations).
Thanks!