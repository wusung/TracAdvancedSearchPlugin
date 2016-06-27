# Created by: 
# Wusung Peng

PORTNAME=	TracAdvancedSearch
PORTVERSION=	0.7.4
CATEGORIES=	www
MASTER_SITES=	https://github.com/wusung/TracAdvancedSearchPlugin/archive/
PKGNAMEPREFIX=  trac-
DISTNAME=       v${PORTVERSION}

MAINTAINER=	wusungpeng@kkbox.com
COMMENT=	Trac plugin for searching tickets with full text search engine.

# LICENSE=	UNKNOWN # Ensure this is valid! See ${PORTSDIR}/Mk/bsd.licenses.db.mk.

RUN_DEPENDS=    tracd:www/trac \
                elasticsearch-py:textproc/py-elasticsearch-py

USES=           python:-2.7
USE_PYTHON=     distutils autoplist

.include <bsd.port.mk>
