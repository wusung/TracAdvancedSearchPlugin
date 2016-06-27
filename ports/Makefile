# Created by: 
# Wusung Peng

PORTNAME=	TracAdvancedSearch
PORTVERSION=	0.7.4
CATEGORIES=	www
MASTER_SITES=	https://github.com/wusung/TracAdvancedSearchPlugin/releases/download/v0.7.4/
PKGNAMEPREFIX=  trac-
DISTNAME=       TracAdvancedSearch-${PORTVERSION}-py2.7

MAINTAINER=	wusungpeng@kkbox.com
COMMENT=	Trac plugin for searching tickets with full text search engine.

# LICENSE=	UNKNOWN # Ensure this is valid! See ${PORTSDIR}/Mk/bsd.licenses.db.mk.

RUN_DEPENDS=    tracd:www/trac \
                pyelasticsearch:textproc/py-pyelasticsearch

USES=           python:-2.7
USE_PYTHON=     distutils autoplist

.include <bsd.port.mk>
