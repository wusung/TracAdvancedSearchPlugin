# Created by: 
# Wusung Peng

PORTNAME=	TracAdvancedSearchPlugin
PORTVERSION=	0.7.4
CATEGORIES=	www
MASTER_SITES=	https://github.com/wusung/TracAdvancedSearchPlugin/releases/download/v${PORTVERSION}/
PKGNAMEPREFIX=  trac-
DISTNAME=       ${PORTNAME}-${PORTVERSION}

MAINTAINER=	wusungpeng@kkbox.com
COMMENT=	Trac plugin for searching tickets with full text search engine.

# LICENSE=	UNKNOWN # Ensure this is valid! See ${PORTSDIR}/Mk/bsd.licenses.db.mk.

RUN_DEPENDS=    tracd:www/trac \
                ${PYTHON_PKGNAMEPREFIX}elasticsearch-py>=2.3.0:textproc/py-elasticsearch-py

USES=           python:-2.7
USE_PYTHON=     distutils autoplist

.include <bsd.port.mk>
