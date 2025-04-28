ARG BASE_TAG="develop"
ARG BASE_IMAGE="core-ubuntu-jammy"
FROM kasmweb/$BASE_IMAGE:$BASE_TAG
USER root

ENV HOME /home/kasm-default-profile
ENV STARTUPDIR /dockerstartup
ENV INST_SCRIPTS $STARTUPDIR/install
ENV ENABLE_REMOTE_DEBUGGING=true
ENV REMOTE_DEBUGGING_PORT=9222
ENV REMOTE_DEBUGGING_ADDRESS=0.0.0.0
ENV KASM_WEB_PORT=6901
WORKDIR $HOME

# Install Brave
COPY ./brave-install-scripts/ $INST_SCRIPTS/brave/
RUN bash $INST_SCRIPTS/brave/install_brave.sh && rm -rf $INST_SCRIPTS/brave/

# Update the desktop environment to be optimized for a single application
RUN cp $HOME/.config/xfce4/xfconf/single-application-xfce-perchannel-xml/* $HOME/.config/xfce4/xfconf/xfce-perchannel-xml/
RUN cp /usr/share/backgrounds/bg_kasm.png /usr/share/backgrounds/bg_default.png
RUN apt-get remove -y xfce4-panel

# Setup the custom startup script
COPY ./custom_startup.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh

ENV KASM_RESTRICTED_FILE_CHOOSER=1

RUN chown 1000:0 $HOME
RUN $STARTUPDIR/set_user_permission.sh $HOME

ENV HOME /home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME

# Expose ports for web access and remote debugging
EXPOSE 6901 5901 9222

USER 1000