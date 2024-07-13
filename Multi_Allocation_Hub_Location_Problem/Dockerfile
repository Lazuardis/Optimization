# Install CBC solver
RUN git clone https://github.com/coin-or/coinbrew /var/cbc
WORKDIR /var/cbc
RUN ./coinbrew fetch Cbc@2.10.5 --no-prompt --no-third-party
RUN ./coinbrew build Cbc --no-prompt --no-third-party --enable-cbc-parallel --prefix=/usr
ENV COIN_INSTALL_DIR /usr

ENV PATH="/var/cbc/build/Cbc/2.10.5/src:${PATH}"