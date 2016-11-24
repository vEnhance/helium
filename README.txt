('-. .-.   ('-.                               _   .-')    
( OO )  / _(  OO)                             ( '.( OO )_  
,--. ,--.(,------.,--.      ,-.-') ,--. ,--.   ,--.   ,--.)
|  | |  | |  .---'|  |.-')  |  |OO)|  | |  |   |   `.'   | 
|   .|  | |  |    |  | OO ) |  |  \|  | | .-') |         | 
|       |(|  '--. |  |`-' | |  |(_/|  |_|( OO )|  |'.'|  | 
|  .-.  | |  .--'(|  '---.',|  |_.'|  | | `-' /|  |   |  | 
|  | |  | |  `---.|      |(_|  |  ('  '-'(_.-' |  |   |  | 
`--' `--' `------'`------'  `--'    `-----'    `--'   `--' 

HELIUM
Copyright (c) 2016 Evan Chen

==========================================================

A manual for users is available in /helium/static/helium-manual/.
Also most of the code is more or less commented thoroughly.
Have fun!

See LICENSE.txt for license details (MIT license).
Note in particular that

> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.


SETUP
==========================================================

If you are using Helium outside of an HMMT context,
you should do the following to get it set up with Django.

1. Create a Django application, as usual
2. Clone the Helium repository into it (say as a submodule), in "helium/"
3. In urls.py, add url(r'^helium/', include('helium.urls')) into urlpatterns.
4. In settings.py, add "helium" to installed applications
5. Configure STATIC and MEDIA settings.
6. Create a base.html template, probably site-wide.
   An example of such a template is given as helium/templates/base.html.EXAMPLE
7. Run migrations (python manage.py migrate)
