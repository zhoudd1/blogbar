# coding: utf-8
import json
from flask import render_template, Blueprint, flash, redirect, url_for, abort, request
from werkzeug.contrib.atom import AtomFeed
from ..models import db, Blog, Post, ApprovementLog, Kind, BlogKind
from ..forms import AddBlogForm
from ..utils.permissions import AdminPermission
from ..utils.helper import parse_int

bp = Blueprint('blog', __name__)


@bp.route('/square')
def square():
    page = request.args.get('page', 1, int)
    kind_id = request.args.get('kind_id', 0, int)
    kinds = Kind.query.order_by(Kind.show_order.asc())
    blogs_query = Blog.query.filter(Blog.is_approved)
    if kind_id:
        blogs = blogs_query.filter(Blog.blog_kinds.any(BlogKind.kind_id == kind_id))
    else:
        blogs = blogs_query
    blogs = blogs.paginate(page, 36)
    latest_blogs = blogs_query.order_by(Blog.created_at.desc()).limit(15)
    return render_template('blog/square.html', blogs=blogs, kinds=kinds, latest_blogs=latest_blogs,
                           kind_id=kind_id)


@bp.route('/<int:uid>', defaults={'page': 1})
@bp.route('/<int:uid>/page/<int:page>')
def view(uid, page):
    blog = Blog.query.get_or_404(uid)
    if not blog.is_approved:
        abort(404)
    posts_count = blog.posts.filter(~Post.hide).count()
    posts = blog.posts
    if not AdminPermission().check():
        posts = posts.filter(~Post.hide)
    posts = posts.order_by(Post.published_at.desc()).paginate(page, 20)
    return render_template('blog/view.html', blog=blog, posts=posts, posts_count=posts_count)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    """推荐博客"""
    kinds = Kind.query.order_by(Kind.show_order.asc())
    form = AddBlogForm()
    form.kinds.choices = [(kind.id, kind.name) for kind in kinds]
    kinds_data = form.kinds.data or []

    if form.validate_on_submit():
        since = parse_int(form.since.data)
        if since is None:
            since = 0
        form.since.data = since
        del form.kinds
        blog = Blog(**form.data)

        for kind_id in kinds_data:  # 添加标签
            blog_kind = BlogKind(kind_id=kind_id)
            blog.blog_kinds.append(blog_kind)

        db.session.add(blog)

        log = ApprovementLog(blog=blog, ip=request.remote_addr)  # 添加log
        db.session.add(log)
        db.session.commit()
        flash('非常感谢你的推荐！我们会在第一时间审核。')
        return redirect(url_for('site.approve_results'))
    return render_template('blog/add.html', form=form, kinds=kinds, kinds_data=kinds_data)


@bp.route('/post/<int:uid>/redirect')
def redirect_post(uid):
    post = Post.query.get_or_404(uid)
    if not post.clicks:
        post.clicks = 0
    post.clicks += 1
    db.session.add(post)
    db.session.commit()
    return redirect(post.url)


@bp.route('/post/<int:uid>')
def post(uid):
    post = Post.query.get_or_404(uid)
    if post.blog.is_protected or not post.blog.is_approved:
        abort(404)
    if post.hide:
        abort(404)
    if post.keywords:
        keywords = json.loads(post.keywords)
        tags = [{'text': tag, 'weight': weight} for tag, weight in keywords]
    else:
        tags = []
    return render_template('blog/post.html', post=post, tags=json.dumps(tags))


@bp.route('/<int:uid>/feed')
def feed(uid):
    blog = Blog.query.get_or_404(uid)
    if not blog.is_approved and not blog.for_special_purpose:
        abort(404)
    if blog.feed:
        abort(404)

    feed = AtomFeed(blog.title, feed_url=request.url, url=blog.url, id=blog.url)
    if blog.subtitle:
        feed.subtitle = blog.subtitle
    for post in blog.posts.filter(~Post.hide). \
            order_by(Post.published_at.desc(), Post.updated_at.desc()).limit(15):
        updated = post.published_at if post.published_at else post.updated_at
        feed.add(post.title, post.content, content_type='html', author=blog.author,
                 url=post.url, id=post.url, updated=updated)
    response = feed.get_response()
    response.headers['Content-Type'] = 'application/xml'
    return response


@bp.route('/posts', defaults={'page': 1})
@bp.route('/posts/page/<int:page>')
def posts(page):
    posts = Post.query. \
        filter(~Post.hide).filter(Post.blog.has(Blog.is_approved)). \
        order_by(Post.published_at.desc()). \
        paginate(page, 20)
    return render_template('blog/posts.html', posts=posts)
